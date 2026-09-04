"""Rule 7 geometry: principal display panel area and required letter height."""
from __future__ import annotations

import math


def pdp_area_cm2(
    shape: str,
    *,
    height_mm: float | None = None,
    width_mm: float | None = None,
    diameter_mm: float | None = None,
    total_surface_cm2: float | None = None,
) -> float:
    """Area of the principal display panel, per Rule 7(4).

    rectangular   height x width of that face
    cylindrical   40 % of (height x circumference)
    other         40 % of the total surface area

    Tops, bottoms, can flanges and the shoulders and necks of bottles and jars
    are excluded; the caller is expected to pass the panel dimensions, not the
    whole pack.
    """
    shape = shape.lower()

    if shape in ("rectangular", "box", "carton", "pouch", "flat"):
        if height_mm is None or width_mm is None:
            raise ValueError("rectangular panel needs height_mm and width_mm")
        return (height_mm * width_mm) / 100.0          # mm^2 -> cm^2

    if shape in ("cylindrical", "bottle", "can", "jar", "tin"):
        if height_mm is None or diameter_mm is None:
            raise ValueError("cylindrical panel needs height_mm and diameter_mm")
        circumference_mm = math.pi * diameter_mm
        return 0.40 * (height_mm * circumference_mm) / 100.0

    if shape in ("other", "irregular"):
        if total_surface_cm2 is None:
            raise ValueError("other shape needs total_surface_cm2")
        return 0.40 * total_surface_cm2

    raise ValueError(f"unknown pack shape: {shape!r}")


def required_letter_height_mm(
    pdp_area_cm2_value: float,
    bands: list[dict],
    surface_type: str = "normal",
) -> float:
    """Minimum letter height for this panel area, from Rule 7 Table-I.

    ``bands`` comes from the JSON rule pack so the table is data, not code.
    """
    if pdp_area_cm2_value is None or pdp_area_cm2_value <= 0:
        raise ValueError("pdp_area_cm2_value must be positive")

    key = "min_height_mm_blown" if surface_type == "blown" else "min_height_mm"
    for band in bands:
        ceiling = band.get("pdp_area_cm2_max")
        if ceiling is None or pdp_area_cm2_value <= ceiling:
            return float(band[key])
    return float(bands[-1][key])


def measured_height_mm(box_height_px: float, mm_per_px: float,
                       padding_factor: float = 1.0) -> float:
    """Convert an OCR box height in pixels to millimetres.

    ``padding_factor`` calibrates for the whitespace most OCR engines include
    around the glyphs. Calibrate it against hand-measured labels and keep the
    value in config rather than inventing one.
    """
    return box_height_px * mm_per_px * padding_factor


def height_verdict(
    measured_mm: float,
    required_mm: float,
    rel_uncertainty: float,
) -> tuple[str, float]:
    """Decide PASS / FAIL / BORDERLINE, honouring the measurement uncertainty.

    Returns the verdict and the absolute uncertainty in millimetres.

    The BORDERLINE band is the point of this function. A reading of 2.4 mm
    against a 2.5 mm requirement, with 5 % uncertainty, genuinely could be
    compliant, and asserting a violation there is how an enforcement tool
    destroys its own credibility.
    """
    tol = measured_mm * rel_uncertainty
    if measured_mm - tol >= required_mm:
        return "PASS", tol
    if measured_mm + tol < required_mm:
        return "FAIL", tol
    return "BORDERLINE", tol
