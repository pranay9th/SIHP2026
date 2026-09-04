"""Rule engine: applicability, exemptions, precedence, and each check kind."""
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from naaptol import rules  # noqa: E402
from naaptol.models import (  # noqa: E402
    FAIL, INDETERMINATE, NOT_APPLICABLE, PASS,
    LabelFacts, PackageContext, ScaleEstimate, TextBox,
)
from naaptol.quality import CaptureQuality  # noqa: E402


@pytest.fixture(scope="module")
def pack():
    return rules.RulePack.load()


@pytest.fixture
def good_scale():
    return ScaleEstimate(0.0846, "aruco_rectified", "measurement", 0.03)


@pytest.fixture
def no_scale():
    return ScaleEstimate(None, "aruco", "none", detail="No marker found.")


@pytest.fixture
def good_quality():
    return CaptureQuality(focus=0.05, contrast=200, ocr_confidence=0.94,
                          text_count=40, resolution_px=1200, grade="good")


@pytest.fixture
def poor_quality():
    return CaptureQuality(focus=0.5, contrast=200, ocr_confidence=0.3,
                          text_count=2, resolution_px=1200, grade="poor",
                          notes="Image is badly out of focus.")


def compliant_facts():
    return LabelFacts(
        raw_text=("Crisp Salted Biscuits Manufactured by: Sunrise Foods, Pune 411019 "
                  "Net Wt. 200 g MRP Rs.40.00 (inclusive of all taxes) Mfd: 03/2026 "
                  "Consumer care: care@sunrise.in"),
        manufacturer="Sunrise Foods, Pune 411019",
        common_name="Crisp Salted Biscuits",
        net_quantity="Net Wt. 200 g",
        net_quantity_value=200.0,
        net_quantity_unit="g",
        net_quantity_context="Net Wt. 200 g MRP Rs.40.00",
        mfg_date="Mfd: 03/2026",
        mrp="MRP Rs.40.00",
        mrp_value=40.0,
        mrp_context="MRP Rs.40.00 (inclusive of all taxes)",
        consumer_care="Consumer care: care@sunrise.in",
        measured_boxes={"mrp": TextBox("Rs.40.00", (10, 10, 90, 37))},
    )


def find(findings, rule_id):
    return next(f for f in findings if f.rule_id == rule_id)


class TestPresenceAndContent:
    def test_compliant_label_passes_everything_applicable(self, pack, good_scale, good_quality):
        ctx = PackageContext(pdp_area_cm2=108, net_quantity_g_or_ml=200)
        out = rules.evaluate(compliant_facts(), ctx, good_scale, pack, quality=good_quality)
        assert [f.rule_id for f in out if f.verdict == FAIL] == []

    def test_missing_mrp_wording_is_flagged_with_its_citation(self, pack, good_scale, good_quality):
        facts = compliant_facts()
        facts.mrp_context = "MRP Rs.99.00"          # no "inclusive of all taxes"
        ctx = PackageContext(pdp_area_cm2=108, net_quantity_g_or_ml=200)
        out = rules.evaluate(facts, ctx, good_scale, pack, quality=good_quality)
        finding = find(out, "LMPC.R6.1.e.mrp_wording")
        assert finding.verdict == FAIL
        assert finding.citation == "Rule 6(1)(e)"

    def test_qualifier_in_net_quantity_is_flagged(self, pack, good_scale, good_quality):
        facts = compliant_facts()
        facts.net_quantity_context = "Net Weight approx. 1500 g"
        ctx = PackageContext(pdp_area_cm2=280, net_quantity_g_or_ml=1500)
        out = rules.evaluate(facts, ctx, good_scale, pack, quality=good_quality)
        assert find(out, "LMPC.R11.no_qualifiers").verdict == FAIL

    @pytest.mark.parametrize("value,unit,verdict", [
        (200, "g", PASS), (1500, "g", FAIL),     # should be 1.5 kg
        (0.5, "kg", FAIL), (1.5, "kg", PASS),
        (250, "ml", PASS), (1200, "ml", FAIL),   # should be 1.2 l
    ])
    def test_unit_rule(self, pack, good_scale, good_quality, value, unit, verdict):
        facts = compliant_facts()
        facts.net_quantity_value, facts.net_quantity_unit = value, unit
        ctx = PackageContext(pdp_area_cm2=108, net_quantity_g_or_ml=200)
        out = rules.evaluate(facts, ctx, good_scale, pack, quality=good_quality)
        assert find(out, "LMPC.R13.units").verdict == verdict

    @pytest.mark.parametrize("price,verdict", [
        (40.0, PASS), (40.5, PASS), (249.75, FAIL), (99.99, FAIL),
    ])
    def test_price_rounding(self, pack, good_scale, good_quality, price, verdict):
        facts = compliant_facts()
        facts.mrp_value = price
        ctx = PackageContext(pdp_area_cm2=108, net_quantity_g_or_ml=200)
        out = rules.evaluate(facts, ctx, good_scale, pack, quality=good_quality)
        assert find(out, "LMPC.R6.1.e.mrp_rounding").verdict == verdict


class TestApplicability:
    def test_country_of_origin_not_applicable_to_domestic_goods(self, pack, good_scale, good_quality):
        ctx = PackageContext(pdp_area_cm2=108, is_imported=False, net_quantity_g_or_ml=200)
        out = rules.evaluate(compliant_facts(), ctx, good_scale, pack, quality=good_quality)
        assert find(out, "LMPC.R6.1.aa.country_of_origin").verdict == NOT_APPLICABLE

    def test_country_of_origin_required_on_imports(self, pack, good_scale, good_quality):
        ctx = PackageContext(pdp_area_cm2=108, is_imported=True, net_quantity_g_or_ml=80)
        out = rules.evaluate(compliant_facts(), ctx, good_scale, pack, quality=good_quality)
        assert find(out, "LMPC.R6.1.aa.country_of_origin").verdict == FAIL

    def test_small_package_exempt_under_rule_26a(self, pack, good_scale, good_quality):
        """A 10 g sachet is outside Chapter II entirely, so nothing may FAIL."""
        facts = LabelFacts(raw_text="Sachet")       # almost nothing declared
        ctx = PackageContext(pdp_area_cm2=20, net_quantity_g_or_ml=8)
        out = rules.evaluate(facts, ctx, good_scale, pack, quality=good_quality)
        assert all(f.verdict == NOT_APPLICABLE for f in out)
        assert "Rule 26(a)" in find(out, "LMPC.R6.1.c.net_quantity").reason

    def test_wholesale_package_skips_retail_only_rules(self, pack, good_scale, good_quality):
        ctx = PackageContext(package_type="wholesale", pdp_area_cm2=2000,
                             net_quantity_g_or_ml=20000)
        out = rules.evaluate(compliant_facts(), ctx, good_scale, pack, quality=good_quality)
        assert find(out, "LMPC.R6.1.e.mrp_present").verdict == NOT_APPLICABLE
        assert find(out, "LMPC.R6.1.c.net_quantity").verdict != NOT_APPLICABLE

    def test_medical_device_yields_to_medical_devices_rules(self, pack, good_scale, good_quality):
        """The 2025 Amendment hands letter sizing to the Medical Devices Rules."""
        ctx = PackageContext(pdp_area_cm2=108, is_medical_device=True,
                             net_quantity_g_or_ml=200)
        out = rules.evaluate(compliant_facts(), ctx, good_scale, pack, quality=good_quality)
        finding = find(out, "LMPC.R7.2.letter_height")
        assert finding.verdict == NOT_APPLICABLE
        assert "Medical Devices Rules" in finding.reason


class TestTemporalVersioning:
    def test_rule_not_yet_in_force_is_skipped(self, pack):
        rule = {"effective_from": "2026-01-01", "effective_to": None}
        assert pack.in_force(rule, date(2025, 6, 1)) is False
        assert pack.in_force(rule, date(2026, 6, 1)) is True

    def test_repealed_rule_is_skipped_after_its_end_date(self, pack):
        rule = {"effective_from": "2011-04-01", "effective_to": "2022-09-30"}
        assert pack.in_force(rule, date(2022, 1, 1)) is True
        assert pack.in_force(rule, date(2023, 1, 1)) is False


class TestNeverGuessAViolation:
    """The safety property the whole design rests on."""

    def test_no_scale_gives_indeterminate_not_fail(self, pack, no_scale, good_quality):
        ctx = PackageContext(pdp_area_cm2=108, net_quantity_g_or_ml=200)
        out = rules.evaluate(compliant_facts(), ctx, no_scale, pack, quality=good_quality)
        assert find(out, "LMPC.R7.2.letter_height").verdict == INDETERMINATE

    def test_unknown_panel_area_gives_indeterminate(self, pack, good_scale, good_quality):
        ctx = PackageContext(pdp_area_cm2=None, net_quantity_g_or_ml=200)
        out = rules.evaluate(compliant_facts(), ctx, good_scale, pack, quality=good_quality)
        assert find(out, "LMPC.R7.2.letter_height").verdict == INDETERMINATE

    def test_indicative_scale_cannot_certify_a_violation(self, pack, good_quality):
        """An undersized reading from a guessed scale is a lead, not a case."""
        weak = ScaleEstimate(0.0846, "pack_width", "indicative", 0.15)
        facts = compliant_facts()
        facts.measured_boxes = {"mrp": TextBox("Rs.40.00", (10, 10, 90, 10))}  # tiny
        ctx = PackageContext(pdp_area_cm2=108, net_quantity_g_or_ml=200)
        out = rules.evaluate(facts, ctx, weak, pack, quality=good_quality)
        assert find(out, "LMPC.R7.2.letter_height").verdict == INDETERMINATE

    def test_poor_photo_cannot_prove_a_declaration_is_missing(self, pack, good_scale, poor_quality):
        """Absence of evidence is not evidence of absence.

        Regression test for a real bug: a defocused photo of a compliant label
        was being reported NON-COMPLIANT because OCR read nothing.
        """
        facts = LabelFacts(raw_text="")             # nothing readable
        ctx = PackageContext(pdp_area_cm2=108, net_quantity_g_or_ml=200)
        out = rules.evaluate(facts, ctx, good_scale, pack, quality=poor_quality)
        assert find(out, "LMPC.R6.1.c.net_quantity").verdict == INDETERMINATE
        assert not any(f.verdict == FAIL for f in out)

    def test_poor_photo_blocks_measurement(self, pack, good_scale, poor_quality):
        ctx = PackageContext(pdp_area_cm2=108, net_quantity_g_or_ml=200)
        out = rules.evaluate(compliant_facts(), ctx, good_scale, pack, quality=poor_quality)
        assert find(out, "LMPC.R7.2.letter_height").verdict == INDETERMINATE


class TestEveryFindingIsExplainable:
    def test_all_findings_carry_a_citation_and_a_reason(self, pack, good_scale, good_quality):
        ctx = PackageContext(pdp_area_cm2=108, net_quantity_g_or_ml=200)
        out = rules.evaluate(compliant_facts(), ctx, good_scale, pack, quality=good_quality)
        assert out, "rule pack produced no findings"
        for finding in out:
            assert finding.citation.startswith("Rule"), finding.rule_id
            assert finding.reason, finding.rule_id
            assert finding.verdict in (PASS, FAIL, NOT_APPLICABLE,
                                       "BORDERLINE", INDETERMINATE)

    def test_failures_carry_a_remedy_and_penalty_exposure(self, pack, good_scale, good_quality):
        facts = compliant_facts()
        facts.mrp_context = "MRP Rs.99.00"
        ctx = PackageContext(pdp_area_cm2=108, net_quantity_g_or_ml=200)
        out = rules.evaluate(facts, ctx, good_scale, pack, quality=good_quality)
        for finding in [f for f in out if f.verdict == FAIL]:
            assert finding.remedy, finding.rule_id
            assert finding.exposure, finding.rule_id
