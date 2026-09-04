"""Recover the millimetres-per-pixel scale of a photograph.

This is the module that turns Naap-Tol from a text reader into a measuring
instrument. Everything downstream that reports a height in millimetres depends
on it, so it is deliberately conservative: when it cannot establish a scale it
says so rather than guessing.

Tier 1  ArUco fiducial of known printed size     -> measurement grade
Tier 2  Known reference object entered by hand   -> measurement grade
Tier 3  Operator supplies the pack width in mm   -> indicative
None    No scale recoverable                     -> INDETERMINATE downstream
"""
from __future__ import annotations

import cv2
import numpy as np

from .models import ScaleEstimate

#: The dictionary the printed reference card uses.
ARUCO_DICT = cv2.aruco.DICT_4X4_50

#: Side length in millimetres of the marker on the printed reference card.
DEFAULT_MARKER_MM = 50.0


def _detector() -> "cv2.aruco.ArucoDetector":
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    params = cv2.aruco.DetectorParameters()
    # Sub-pixel corner refinement materially improves the measurement, which is
    # the whole point of this module.
    params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    return cv2.aruco.ArucoDetector(dictionary, params)


def generate_marker(marker_id: int = 0, side_px: int = 600) -> np.ndarray:
    """Render a marker image, for printing the reference card."""
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    return cv2.aruco.generateImageMarker(dictionary, marker_id, side_px)


def detect_marker_px(image: np.ndarray) -> tuple[float, np.ndarray] | None:
    """Return (mean side length in pixels, corner array) for the first marker.

    The mean of the four sides is used rather than a single side, so mild
    perspective is averaged out instead of biasing the result one way.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    corners, ids, _ = _detector().detectMarkers(gray)
    if ids is None or len(corners) == 0:
        return None

    pts = corners[0].reshape(4, 2).astype(np.float64)
    sides = [float(np.linalg.norm(pts[i] - pts[(i + 1) % 4])) for i in range(4)]
    return float(np.mean(sides)), pts


def _squareness(pts: np.ndarray) -> float:
    """0.0 means a perfect square; larger means more perspective distortion."""
    sides = [float(np.linalg.norm(pts[i] - pts[(i + 1) % 4])) for i in range(4)]
    return float(np.std(sides) / np.mean(sides)) if np.mean(sides) else 1.0


def estimate_from_aruco(
    image: np.ndarray, marker_mm: float = DEFAULT_MARKER_MM
) -> ScaleEstimate:
    """Tier 1. Find the printed marker and derive mm-per-pixel from it."""
    found = detect_marker_px(image)
    if found is None:
        return ScaleEstimate(
            mm_per_px=None,
            method="aruco",
            grade="none",
            detail="No ArUco reference marker found in the image.",
        )

    side_px, pts = found
    if side_px < 40:
        return ScaleEstimate(
            mm_per_px=None,
            method="aruco",
            grade="none",
            detail=f"Marker found but too small to measure from ({side_px:.0f} px "
                   f"across). Move the camera closer.",
        )

    skew = _squareness(pts)
    mm_per_px = marker_mm / side_px

    # A skewed marker means the camera was not parallel to the pack, which
    # biases every height measurement. Past a threshold we refuse to certify.
    if skew > 0.08:
        return ScaleEstimate(
            mm_per_px=mm_per_px,
            method="aruco",
            grade="indicative",
            rel_uncertainty=max(0.05, skew),
            detail=f"Marker is noticeably skewed ({skew * 100:.1f} % side variation). "
                   f"Re-shoot square-on for a measurement-grade result.",
        )

    # Corner localisation is good to well under a pixel with sub-pixel
    # refinement; 1 px of total error over the measured side is a safe envelope.
    rel = max(1.0 / side_px, 0.01)
    return ScaleEstimate(
        mm_per_px=mm_per_px,
        method="aruco",
        grade="measurement",
        rel_uncertainty=rel,
        detail=f"{marker_mm:.0f} mm marker measured {side_px:.1f} px across, "
               f"so 1 px = {mm_per_px:.4f} mm.",
    )


def estimate_from_reference_width(
    known_mm: float, measured_px: float, label: str = "reference object"
) -> ScaleEstimate:
    """Tier 2. The operator marked a reference object of known size."""
    if measured_px <= 0 or known_mm <= 0:
        return ScaleEstimate(None, "reference_object", "none",
                             detail="Invalid reference measurement.")
    return ScaleEstimate(
        mm_per_px=known_mm / measured_px,
        method="reference_object",
        grade="measurement",
        rel_uncertainty=0.03,
        detail=f"{label} of {known_mm:.2f} mm measured {measured_px:.1f} px.",
    )


def estimate_from_pack_width(image_width_px: int, pack_width_mm: float) -> ScaleEstimate:
    """Tier 3. Operator typed the pack width; the pack fills the frame.

    Never measurement grade: it assumes the pack spans the full image, which is
    rarely exactly true.
    """
    if pack_width_mm <= 0 or image_width_px <= 0:
        return ScaleEstimate(None, "pack_width", "none",
                             detail="Invalid pack width.")
    return ScaleEstimate(
        mm_per_px=pack_width_mm / image_width_px,
        method="pack_width",
        grade="indicative",
        rel_uncertainty=0.15,
        detail=f"Assumed the {pack_width_mm:.0f} mm pack spans the full "
               f"{image_width_px} px frame. Indicative only.",
    )


def rectify(
    image: np.ndarray,
    marker_mm: float = DEFAULT_MARKER_MM,
    target_px: int = 600,
    max_side: int = 6000,
) -> tuple[np.ndarray, ScaleEstimate] | None:
    """Flatten the photograph using the marker, then derive an exact scale.

    The marker is a known square. The homography that maps its four detected
    corners back to a perfect square also removes the perspective distortion
    from the rest of the (coplanar) scene. Measuring in the rectified plane is
    what makes a hand-held, slightly tilted photograph usable.

    Without this step a 5 degree tilt inflates measured letter heights by
    roughly 7 %, which is larger than the margin most Rule 7 decisions turn on.

    Assumes the reference card is lying in the same plane as the panel being
    measured, which is what the capture instructions ask the operator to do.
    Returns None when no marker is present.
    """
    found = detect_marker_px(image)
    if found is None:
        return None

    _, pts = found
    dst = np.float32([[0, 0], [target_px, 0],
                      [target_px, target_px], [0, target_px]])
    homography = cv2.getPerspectiveTransform(pts.astype(np.float32), dst)

    # Warp the whole frame, not just the marker, and shift it back into view.
    h, w = image.shape[:2]
    frame = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    warped = cv2.perspectiveTransform(frame, homography).reshape(-1, 2)
    min_x, min_y = warped.min(axis=0)
    max_x, max_y = warped.max(axis=0)

    out_w = int(min(max(max_x - min_x, 1), max_side))
    out_h = int(min(max(max_y - min_y, 1), max_side))
    shift = np.array([[1, 0, -min_x], [0, 1, -min_y], [0, 0, 1]], np.float32)

    rectified = cv2.warpPerspective(
        image, shift @ homography, (out_w, out_h),
        flags=cv2.INTER_CUBIC, borderValue=(238, 238, 234),
    )

    mm_per_px = marker_mm / target_px
    estimate_obj = ScaleEstimate(
        mm_per_px=mm_per_px,
        method="aruco_rectified",
        grade="measurement",
        # Dominated by box localisation, about one pixel. Measured at 0.05 mm
        # worst case on the synthetic set; 3 % is a deliberately safe envelope.
        rel_uncertainty=0.03,
        detail=f"Image rectified on the {marker_mm:.0f} mm marker; "
               f"1 px = {mm_per_px:.4f} mm in the flattened plane.",
    )
    return rectified, estimate_obj


def estimate(
    image: np.ndarray,
    marker_mm: float = DEFAULT_MARKER_MM,
    pack_width_mm: float | None = None,
) -> ScaleEstimate:
    """Run the cascade and return the best scale available."""
    est = estimate_from_aruco(image, marker_mm)
    if est.usable and est.grade == "measurement":
        return est

    if pack_width_mm:
        fallback = estimate_from_pack_width(image.shape[1], pack_width_mm)
        # Keep a skewed-but-present marker over a typed-in guess.
        if est.usable:
            return est
        return fallback

    return est
