"""One function that takes an image and returns a report card."""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from . import extract as extract_mod
from . import ocr as ocr_mod
from . import scale as scale_mod
from .models import PackageContext, ScanResult
from .rules import RulePack

#: Calibration for the gap between an ink-tight OCR box and true cap height.
#: 1.0 means the tightened box is taken as the letter height. Re-derive this
#: from hand-measured labels rather than trusting the default.
DEFAULT_PADDING_FACTOR = 1.0


def sha256_of(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


def load_image(path: str | Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return image


def scan(
    image: np.ndarray,
    ctx: PackageContext,
    *,
    backend: ocr_mod.OcrBackend | None = None,
    rule_pack: RulePack | None = None,
    marker_mm: float = scale_mod.DEFAULT_MARKER_MM,
    pack_width_mm: float | None = None,
    padding_factor: float = DEFAULT_PADDING_FACTOR,
    image_bytes: bytes | None = None,
) -> ScanResult:
    """Run the whole pipeline: measure, read, extract, adjudicate."""
    from . import quality as quality_mod
    from .rules import evaluate

    rule_pack = rule_pack or RulePack.load()

    # 1. Flatten the photograph on the marker. This removes the perspective
    #    error that a hand-held shot introduces, and yields an exact scale.
    #    Everything downstream then measures in the rectified plane.
    working = image
    rectified = scale_mod.rectify(image, marker_mm)
    if rectified is not None:
        working, scale_estimate = rectified
    else:
        scale_estimate = scale_mod.estimate(image, marker_mm, pack_width_mm)

    # 2. Read the text.
    boxes = ocr_mod.read_text(working, backend=backend)

    # 3. Decide whether this photograph can support a conclusion at all.
    capture = quality_mod.assess(working, boxes)

    # 4. Extract and adjudicate.
    facts = extract_mod.extract(boxes)
    findings = evaluate(facts, ctx, scale_estimate, rule_pack,
                        padding_factor, quality=capture)

    return ScanResult(
        findings=findings,
        facts=facts,
        context=ctx,
        scale=scale_estimate,
        quality=capture,
        working_image=working,
        rule_pack_version=rule_pack.version,
        image_sha256=sha256_of(image_bytes) if image_bytes else "",
        scanned_at=datetime.now().isoformat(timespec="seconds"),
    )


def annotate(image: np.ndarray, result: ScanResult) -> np.ndarray:
    """Draw the measured declarations onto a copy of the image, for evidence."""
    out = image.copy()
    colours = {"PASS": (90, 160, 60), "FAIL": (40, 40, 200),
               "BORDERLINE": (30, 160, 220), "INDETERMINATE": (150, 150, 150)}

    for finding in result.findings:
        if not finding.evidence_bbox:
            continue
        x, y, w, h = finding.evidence_bbox
        colour = colours.get(finding.verdict, (120, 120, 120))
        cv2.rectangle(out, (x, y), (x + w, y + h), colour, 2)
        if finding.measured:
            cv2.putText(out, finding.measured, (x, max(14, y - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 1, cv2.LINE_AA)
    return out
