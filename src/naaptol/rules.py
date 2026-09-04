"""The rule engine.

Rules are data, loaded from config/rules/*.json, not code. That is what lets a
Legal Metrology officer amend the rule pack without a developer, and what lets
the system judge a package by the rules in force on the date it was packed.

Order of evaluation for every rule:
    1. Is the rule in force on the pack date?      -> else skip
    2. Does it apply to this package type?         -> else NOT_APPLICABLE
    3. Is the package exempt (Rule 26)?            -> else NOT_APPLICABLE
    4. Does another regime take precedence?        -> else NOT_APPLICABLE
    5. Only then, is it complied with?
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path

from . import geometry
from .models import (
    BORDERLINE, FAIL, INDETERMINATE, NOT_APPLICABLE, PASS,
    Finding, LabelFacts, PackageContext, ScaleEstimate,
)

DEFAULT_RULE_PACK = (
    Path(__file__).resolve().parents[2] / "config" / "rules" / "lmpc-2011.json"
)


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

class RulePack:
    def __init__(self, data: dict):
        self.data = data
        self.version = data.get("version", "0.0.0")
        self.rules = data.get("rules", [])
        self.bands = data["letter_height_table"]["bands"]
        self.height_citation = data["letter_height_table"]["citation"]

    @classmethod
    def load(cls, path: str | Path | None = None) -> "RulePack":
        path = Path(path) if path else DEFAULT_RULE_PACK
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def in_force(self, rule: dict, on: date | None) -> bool:
        """Is this rule in force on the given date?"""
        if on is None:
            return rule.get("effective_to") is None
        start = rule.get("effective_from")
        end = rule.get("effective_to")
        if start and on < _as_date(start):
            return False
        if end and on > _as_date(end):
            return False
        return True


def _as_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


# --------------------------------------------------------------------------
# Exemptions, Rule 26
# --------------------------------------------------------------------------

def exemption_for(ctx: PackageContext) -> dict | None:
    """Return the exemption that removes this package from Chapter II, if any."""
    q = ctx.net_quantity_g_or_ml
    if q is not None and q <= 10:
        return {
            "id": "LMPC.R26.a",
            "citation": "Rule 26(a)",
            "reason": f"Net quantity {q:g} g/ml is 10 g/ml or less, so the package "
                      f"is exempt from the Chapter II declarations.",
        }
    if ctx.commodity_category == "fast_food":
        return {
            "id": "LMPC.R26.b",
            "citation": "Rule 26(b)",
            "reason": "Fast food packed by a restaurant or hotel is exempt.",
        }
    if ctx.commodity_category == "agricultural" and q is not None and q > 50_000:
        return {
            "id": "LMPC.R26.d",
            "citation": "Rule 26(d)",
            "reason": "Agricultural farm produce in a package above 50 kg is exempt.",
        }
    return None


# --------------------------------------------------------------------------
# Individual checks
# --------------------------------------------------------------------------

def _presence(rule: dict, facts: LabelFacts) -> tuple[str, str]:
    value = getattr(facts, rule["field"], None)
    if value:
        shown = str(value)
        if len(shown) > 70:
            shown = shown[:67] + "..."
        return PASS, f"Found: {shown}"
    return FAIL, f"No {rule['title'].lower()} could be read from the label."


def _pattern(rule: dict, facts: LabelFacts) -> tuple[str, str]:
    gate = rule.get("requires_field")
    if gate and not getattr(facts, gate, None):
        return NOT_APPLICABLE, f"Not checked, because no {gate.replace('_', ' ')} was found."

    haystack = getattr(facts, rule["field"], None) or ""
    if re.search(rule["pattern"], haystack):
        return PASS, "Required wording is present."
    return FAIL, "Required wording is absent from the declaration."


def _forbidden_pattern(rule: dict, facts: LabelFacts) -> tuple[str, str]:
    gate = rule.get("requires_field")
    if gate and not getattr(facts, gate, None):
        return NOT_APPLICABLE, f"Not checked, because no {gate.replace('_', ' ')} was found."

    haystack = getattr(facts, rule["field"], None) or ""
    hit = re.search(rule["pattern"], haystack)
    if hit:
        return FAIL, f"Prohibited wording found: {hit.group(0)!r}"
    return PASS, "No prohibited wording found."


def _rounding(rule: dict, facts: LabelFacts) -> tuple[str, str]:
    value = getattr(facts, rule["field"], None)
    if value is None:
        return NOT_APPLICABLE, "No price value could be read."
    paise = round(round(float(value), 2) * 100) % 100
    if paise in rule.get("allowed_remainders_paise", [0, 50]):
        return PASS, f"Rs {value:.2f} is rounded to the nearest rupee or 50 paise."
    return FAIL, f"Rs {value:.2f} is not rounded to the nearest rupee or 50 paise."


def _unit_check(rule: dict, facts: LabelFacts) -> tuple[str, str]:
    value, unit = facts.net_quantity_value, facts.net_quantity_unit
    if value is None or unit is None:
        return NOT_APPLICABLE, "Net quantity could not be parsed."

    if unit == "g" and value >= 1000:
        return FAIL, f"{value:g} g should be declared as {value / 1000:g} kg."
    if unit == "ml" and value >= 1000:
        return FAIL, f"{value:g} ml should be declared as {value / 1000:g} l."
    if unit == "kg" and value < 1:
        return FAIL, f"{value:g} kg should be declared as {value * 1000:g} g."
    if unit == "l" and value < 1:
        return FAIL, f"{value:g} l should be declared as {value * 1000:g} ml."
    if unit == "mg":
        return FAIL, "Weight below 1 kg must be declared in grams, not milligrams."
    return PASS, f"{value:g} {unit} uses the correct unit for its magnitude."


def _language(rule: dict, facts: LabelFacts) -> tuple[str, str]:
    from .extract import dominant_script
    script = dominant_script(facts.raw_text)
    if script == "unknown":
        return INDETERMINATE, "No readable text, so the script cannot be determined."
    if script in ("latin", "devanagari", "mixed"):
        return PASS, f"Declarations are in {script} script, which is permitted."
    return FAIL, f"Declarations appear to be in {script} script only."


def _letter_height(
    rule: dict, facts: LabelFacts, ctx: PackageContext,
    scale: ScaleEstimate, bands: list[dict], padding_factor: float,
    quality: "CaptureQuality | None" = None,
) -> tuple[str, str, str | None, str | None, tuple | None]:
    """The Rule 7 measurement. Returns verdict, reason, measured, required, bbox."""
    if quality is not None and not quality.trust_measurement:
        return (
            INDETERMINATE,
            f"Cannot measure reliably from this image: {quality.notes} "
            f"Re-shoot square-on, in better light, with the reference card in frame.",
            None, None, None,
        )

    if not scale.usable:
        return (
            INDETERMINATE,
            f"Cannot measure: {scale.detail or 'no scale reference in the image.'} "
            f"Place the printed reference card beside the pack and re-shoot.",
            None, None, None,
        )

    if ctx.pdp_area_cm2 is None:
        return (
            INDETERMINATE,
            "Cannot measure: the principal display panel area is unknown. "
            "Enter the pack shape and dimensions.",
            None, None, None,
        )

    required = geometry.required_letter_height_mm(
        ctx.pdp_area_cm2, bands, ctx.surface_type
    )

    # Judge the smallest of the measured declarations: if the smallest passes,
    # all of them do.
    worst = None
    for field_name in rule.get("measured_fields", []):
        box = facts.measured_boxes.get(field_name)
        if box is None:
            continue
        mm = geometry.measured_height_mm(box.height_px, scale.mm_per_px, padding_factor)
        if worst is None or mm < worst[1]:
            worst = (field_name, mm, box)

    if worst is None:
        return (
            INDETERMINATE,
            "No measurable declaration was located on the panel.",
            None, f"{required:.1f} mm", None,
        )

    field_name, mm, box = worst
    verdict, tol = geometry.height_verdict(mm, required, scale.rel_uncertainty)

    # An indicative scale can never certify a violation.
    if verdict == FAIL and scale.grade != "measurement":
        verdict = INDETERMINATE
        reason = (
            f"{field_name.replace('_', ' ')} measures about {mm:.2f} mm against a "
            f"{required:.1f} mm requirement, but the scale is only "
            f"{scale.grade} grade ({scale.method}). Physical verification required."
        )
    elif verdict == FAIL:
        reason = (
            f"{field_name.replace('_', ' ')} letter height is {mm:.2f} "
            f"+/- {tol:.2f} mm, below the {required:.1f} mm required for a "
            f"{ctx.pdp_area_cm2:.0f} cm2 principal display panel."
        )
    elif verdict == BORDERLINE:
        reason = (
            f"{field_name.replace('_', ' ')} letter height is {mm:.2f} "
            f"+/- {tol:.2f} mm against a {required:.1f} mm requirement. The "
            f"measurement straddles the threshold, so this needs a physical check."
        )
    else:
        reason = (
            f"{field_name.replace('_', ' ')} letter height is {mm:.2f} "
            f"+/- {tol:.2f} mm, at or above the {required:.1f} mm required."
        )

    return verdict, reason, f"{mm:.2f} mm", f"{required:.1f} mm", box.bbox


def _letter_width(
    rule: dict, facts: LabelFacts, scale: ScaleEstimate,
) -> tuple[str, str, str | None, str | None]:
    """Rule 7(3): character width at least one third of character height.

    Uses the per-glyph ratio measured during OCR. Note that this rule is
    checked on the ratio alone, so it does not need a millimetre scale.
    """
    ratios = [
        (name, box.char_width_ratio)
        for name, box in facts.measured_boxes.items()
        if box.char_width_ratio is not None
    ]
    if not ratios:
        return (INDETERMINATE,
                "Characters could not be segmented, so width cannot be measured.",
                None, None)

    field_name, ratio = min(ratios, key=lambda t: t[1])
    minimum = float(rule.get("min_width_ratio", 1 / 3))
    if ratio >= minimum:
        return (PASS,
                f"{field_name.replace('_', ' ')} median character width is "
                f"{ratio:.2f} of its height.",
                f"{ratio:.2f}", f"{minimum:.2f}")
    return (FAIL,
            f"{field_name.replace('_', ' ')} median character width is only "
            f"{ratio:.2f} of its height.",
            f"{ratio:.2f}", f"{minimum:.2f}")


# --------------------------------------------------------------------------
# Engine
# --------------------------------------------------------------------------

def evaluate(
    facts: LabelFacts,
    ctx: PackageContext,
    scale: ScaleEstimate,
    pack: RulePack | None = None,
    padding_factor: float = 1.0,
    quality: "CaptureQuality | None" = None,
) -> list[Finding]:
    """Run every applicable rule and return the report card."""
    pack = pack or RulePack.load()
    exemption = exemption_for(ctx)
    findings: list[Finding] = []

    for rule in pack.rules:
        if not pack.in_force(rule, ctx.packed_on):
            continue

        base = dict(
            rule_id=rule["id"],
            citation=rule["citation"],
            title=rule["title"],
            severity=rule.get("severity", "minor"),
            remedy=rule.get("remedy", ""),
            exposure=rule.get("exposure", ""),
        )

        # 2. package type
        types = rule.get("applies_to_package_types", ["retail"])
        if ctx.package_type not in types:
            findings.append(Finding(
                verdict=NOT_APPLICABLE,
                reason=f"Does not apply to a {ctx.package_type} package.",
                **base,
            ))
            continue

        # 3. exemption
        if exemption:
            findings.append(Finding(
                verdict=NOT_APPLICABLE,
                reason=f"Exempt under {exemption['citation']}. {exemption['reason']}",
                **base,
            ))
            continue

        # 4. precedence, e.g. medical devices after the 2025 Amendment
        yields_to = rule.get("precedence_yields_to") or []
        if yields_to and ctx.is_medical_device:
            other = yields_to[0]
            findings.append(Finding(
                verdict=NOT_APPLICABLE,
                reason=f"{other['regime']} prevails for medical devices "
                       f"({other['citation']}).",
                **base,
            ))
            continue

        # conditional rules, e.g. country of origin only for imports
        cond = rule.get("condition") or {}
        skip = False
        for key, want in cond.items():
            if getattr(ctx, key, None) != want:
                findings.append(Finding(
                    verdict=NOT_APPLICABLE,
                    reason=f"Applies only when {key.replace('_', ' ')} is {want}.",
                    **base,
                ))
                skip = True
                break
        if skip:
            continue

        # 5. the actual check
        kind = rule["kind"]
        measured = required = None
        bbox = None

        if kind == "presence":
            verdict, reason = _presence(rule, facts)
        elif kind == "pattern":
            verdict, reason = _pattern(rule, facts)
        elif kind == "forbidden_pattern":
            verdict, reason = _forbidden_pattern(rule, facts)
        elif kind == "rounding":
            verdict, reason = _rounding(rule, facts)
        elif kind == "unit_check":
            verdict, reason = _unit_check(rule, facts)
        elif kind == "language":
            verdict, reason = _language(rule, facts)
        elif kind == "letter_height":
            verdict, reason, measured, required, bbox = _letter_height(
                rule, facts, ctx, scale, pack.bands, padding_factor, quality
            )
        elif kind == "letter_width":
            verdict, reason, measured, required = _letter_width(rule, facts, scale)
        else:
            verdict, reason = INDETERMINATE, f"Unknown rule kind {kind!r}."

        # A poor photograph cannot prove a declaration is missing. Downgrade
        # any "absence" FAIL to INDETERMINATE so the officer re-shoots rather
        # than acting on an unreadable image.
        if (verdict == FAIL and quality is not None
                and not quality.trust_absence
                and kind in ("presence", "pattern", "forbidden_pattern")):
            verdict = INDETERMINATE
            reason = (f"Cannot conclude from this image: {quality.notes} "
                      f"Original check said: {reason}")

        findings.append(Finding(
            verdict=verdict, reason=reason, measured=measured,
            required=required, evidence_bbox=bbox, **base,
        ))

    findings.sort(key=lambda f: f.sort_key)
    return findings
