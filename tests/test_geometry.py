"""Rule 7 geometry: panel area and the letter-height table."""
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from naaptol import geometry  # noqa: E402

BANDS = json.loads(
    (ROOT / "config" / "rules" / "lmpc-2011.json").read_text(encoding="utf-8")
)["letter_height_table"]["bands"]


class TestPdpArea:
    def test_rectangular_is_height_times_width(self):
        # 120 mm x 90 mm = 10 800 mm2 = 108 cm2
        assert geometry.pdp_area_cm2(
            "rectangular", height_mm=120, width_mm=90
        ) == pytest.approx(108.0)

    def test_cylindrical_is_forty_percent_of_height_times_circumference(self):
        # Rule 7(4): 40 % of (height x circumference)
        height, diameter = 150.0, 60.0
        expected = 0.40 * height * math.pi * diameter / 100.0
        assert geometry.pdp_area_cm2(
            "cylindrical", height_mm=height, diameter_mm=diameter
        ) == pytest.approx(expected)

    def test_other_shape_is_forty_percent_of_total_surface(self):
        assert geometry.pdp_area_cm2(
            "other", total_surface_cm2=500
        ) == pytest.approx(200.0)

    def test_unknown_shape_raises(self):
        with pytest.raises(ValueError):
            geometry.pdp_area_cm2("dodecahedron", height_mm=10, width_mm=10)

    def test_missing_dimension_raises(self):
        with pytest.raises(ValueError):
            geometry.pdp_area_cm2("rectangular", height_mm=10)


class TestRequiredHeight:
    @pytest.mark.parametrize("area,expected", [
        (10, 1.0), (50, 1.0),          # band 1 boundary
        (50.1, 1.5), (100, 1.5),       # band 2 boundary
        (100.1, 2.5), (500, 2.5),      # band 3 boundary
        (500.1, 4.0), (2500, 4.0),     # band 4 boundary
        (2500.1, 6.0), (99999, 6.0),   # band 5
    ])
    def test_table_one_bands(self, area, expected):
        assert geometry.required_letter_height_mm(area, BANDS) == expected

    @pytest.mark.parametrize("area,expected", [
        (50, 1.5), (100, 3.0), (500, 4.0), (2500, 6.0), (5000, 6.0),
    ])
    def test_blown_or_moulded_column(self, area, expected):
        assert geometry.required_letter_height_mm(area, BANDS, "blown") == expected

    def test_zero_area_rejected(self):
        with pytest.raises(ValueError):
            geometry.required_letter_height_mm(0, BANDS)


class TestHeightVerdict:
    def test_clearly_above_passes(self):
        verdict, _ = geometry.height_verdict(3.0, 2.5, 0.03)
        assert verdict == "PASS"

    def test_clearly_below_fails(self):
        verdict, _ = geometry.height_verdict(1.8, 2.5, 0.03)
        assert verdict == "FAIL"

    def test_straddling_the_threshold_is_borderline_not_fail(self):
        """The single most important behaviour in the project.

        2.45 mm measured against 2.5 mm required, with 3 % uncertainty, spans
        the threshold. Calling that a violation would put an honest trader in
        front of a prosecution on a measurement that cannot support it.
        """
        verdict, tol = geometry.height_verdict(2.45, 2.5, 0.03)
        assert verdict == "BORDERLINE"
        assert tol == pytest.approx(2.45 * 0.03)

    def test_higher_uncertainty_widens_the_borderline_band(self):
        # Same reading, worse instrument: must not harden into a FAIL.
        assert geometry.height_verdict(2.2, 2.5, 0.02)[0] == "FAIL"
        assert geometry.height_verdict(2.2, 2.5, 0.20)[0] == "BORDERLINE"

    def test_exactly_at_threshold_with_no_uncertainty_passes(self):
        assert geometry.height_verdict(2.5, 2.5, 0.0)[0] == "PASS"
