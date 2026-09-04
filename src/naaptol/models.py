"""Data structures shared across the pipeline.

Deliberately plain dataclasses, no pydantic, so a first-year reader can follow
exactly what is stored where.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Any


# --------------------------------------------------------------------------
# Verdicts
# --------------------------------------------------------------------------

PASS = "PASS"
FAIL = "FAIL"
NOT_APPLICABLE = "NOT_APPLICABLE"
BORDERLINE = "BORDERLINE"
INDETERMINATE = "INDETERMINATE"

#: Ordering used when sorting a report card, most serious first.
VERDICT_ORDER = {FAIL: 0, BORDERLINE: 1, INDETERMINATE: 2, PASS: 3, NOT_APPLICABLE: 4}

SEVERITY_ORDER = {"critical": 0, "major": 1, "minor": 2}


# --------------------------------------------------------------------------
# Perception layer
# --------------------------------------------------------------------------

@dataclass
class TextBox:
    """One piece of text found on the label, with its pixel geometry."""

    text: str
    #: (x, y, width, height) in pixels, axis aligned.
    bbox: tuple[int, int, int, int]
    confidence: float = 1.0
    #: Median glyph width / glyph height, for Rule 7(3). None if unmeasurable.
    char_width_ratio: float | None = None

    @property
    def height_px(self) -> int:
        return self.bbox[3]

    @property
    def width_px(self) -> int:
        return self.bbox[2]


@dataclass
class ScaleEstimate:
    """How many millimetres one pixel represents, and how much we trust it.

    ``grade`` drives what the system is allowed to say. Only measurement-grade
    scale may support an enforcement verdict; anything weaker downgrades a
    geometric FAIL to INDETERMINATE.
    """

    mm_per_px: float | None
    method: str
    #: "measurement" | "indicative" | "none"
    grade: str
    #: Relative uncertainty, e.g. 0.02 means +/- 2 %.
    rel_uncertainty: float = 0.0
    detail: str = ""

    @property
    def usable(self) -> bool:
        return self.mm_per_px is not None and self.mm_per_px > 0


# --------------------------------------------------------------------------
# Extraction layer
# --------------------------------------------------------------------------

@dataclass
class LabelFacts:
    """Normalised declarations read off one package."""

    raw_text: str = ""
    boxes: list[TextBox] = field(default_factory=list)

    manufacturer: str | None = None
    country_of_origin: str | None = None
    common_name: str | None = None

    net_quantity: str | None = None
    net_quantity_value: float | None = None
    net_quantity_unit: str | None = None
    net_quantity_context: str | None = None

    mfg_date: str | None = None
    best_before: str | None = None

    mrp: str | None = None
    mrp_value: float | None = None
    mrp_context: str | None = None

    consumer_care: str | None = None

    #: Box that carried each measured declaration, for the geometry rules.
    measured_boxes: dict[str, TextBox] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("boxes", None)
        d.pop("measured_boxes", None)
        return d


@dataclass
class PackageContext:
    """What the operator tells us about the package before we judge it."""

    package_type: str = "retail"          # retail | wholesale | export
    pdp_area_cm2: float | None = None
    surface_type: str = "normal"          # normal | blown
    is_imported: bool = False
    is_medical_device: bool = False
    commodity_category: str = "general"
    packed_on: date | None = None         # governs which rule version applies
    net_quantity_g_or_ml: float | None = None


# --------------------------------------------------------------------------
# Adjudication layer
# --------------------------------------------------------------------------

@dataclass
class Finding:
    """The outcome of one rule against one package."""

    rule_id: str
    citation: str
    title: str
    verdict: str
    severity: str
    reason: str
    remedy: str = ""
    exposure: str = ""
    measured: str | None = None
    required: str | None = None
    evidence_bbox: tuple[int, int, int, int] | None = None

    @property
    def sort_key(self) -> tuple[int, int]:
        return (
            VERDICT_ORDER.get(self.verdict, 9),
            SEVERITY_ORDER.get(self.severity, 9),
        )


@dataclass
class ScanResult:
    """Everything produced for one scanned package."""

    findings: list[Finding]
    facts: LabelFacts
    context: PackageContext
    scale: ScaleEstimate
    rule_pack_version: str
    #: Capture quality; typed loosely to keep models.py free of cv2 imports.
    quality: Any = None
    #: The rectified image the measurements were actually taken from.
    working_image: Any = None
    image_sha256: str = ""
    scanned_at: str = ""

    # -- summary helpers ---------------------------------------------------

    def count(self, verdict: str) -> int:
        return sum(1 for f in self.findings if f.verdict == verdict)

    @property
    def declarations_present(self) -> int:
        """How many of the nine Rule 6(1) declarations were found."""
        names = [
            "manufacturer", "common_name", "net_quantity", "mfg_date",
            "mrp", "consumer_care",
        ]
        n = sum(1 for k in names if getattr(self.facts, k))
        if self.context.is_imported:
            if self.facts.country_of_origin:
                n += 1
        else:
            n += 1  # not applicable, counts as satisfied
        if self.facts.best_before:
            n += 1
        # dimensions, where relevant, is treated as satisfied by default
        n += 1
        return min(n, 9)

    @property
    def overall(self) -> str:
        if self.count(FAIL):
            return "NON-COMPLIANT"
        if self.count(BORDERLINE) or self.count(INDETERMINATE):
            return "NEEDS PHYSICAL CHECK"
        return "COMPLIANT"
