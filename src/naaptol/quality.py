"""Judge whether a photograph is good enough to draw conclusions from.

This module exists because of a bug found by the project's own robustness
check: a defocused photograph of a fully COMPLIANT label was being reported as
NON-COMPLIANT. Text went unread, so declarations looked absent, and a softened
glyph edge measured short. Both are failures of the photograph, not of the
package, and a system that cannot tell the difference will accuse honest
traders.

So capture quality is measured first, and it can veto a verdict. Poor input
produces INDETERMINATE, never FAIL.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .models import TextBox


@dataclass
class CaptureQuality:
    focus: float          # 0 sharp .. 1 very soft (fraction of pixels mid-tone)
    contrast: float       # background-to-ink separation, 0..255
    ocr_confidence: float # mean confidence over recognised boxes, 0..1
    text_count: int
    resolution_px: int    # shorter side of the image

    #: "good" | "marginal" | "poor"
    grade: str = "good"
    notes: str = ""

    @property
    def trust_absence(self) -> bool:
        """May a missing declaration be reported as a genuine FAIL?

        Only when the image is good enough that the text would have been read
        had it been printed. Otherwise absence of evidence is not evidence of
        absence.
        """
        return self.grade == "good"

    @property
    def trust_measurement(self) -> bool:
        """May a millimetre measurement support an enforcement verdict?"""
        return self.grade in ("good", "marginal")


# Thresholds calibrated on the synthetic sample set. Re-derive them on real
# photographs before quoting any accuracy figure from field use.
FOCUS_MARGINAL = 0.12
FOCUS_POOR = 0.30
CONF_MARGINAL = 0.80
CONF_POOR = 0.60
MIN_RESOLUTION = 600


def soft_edge_fraction(gray: np.ndarray) -> float:
    """Fraction of pixels sitting between the ink and background levels.

    A sharp image is almost all ink or almost all background, with a thin
    transition. Defocus widens that transition, so this number rises. Unlike
    Laplacian variance it is not inflated by sensor noise, which matters
    because a noisy phone photo in a dim shop must not be mistaken for a
    sharp one.
    """
    background = float(np.percentile(gray, 95))
    ink = float(np.percentile(gray, 5))
    span = background - ink
    if span < 15:
        return 1.0
    low, high = ink + 0.25 * span, background - 0.25 * span
    return float(np.mean((gray > low) & (gray < high)))


def assess(image: np.ndarray, boxes: list[TextBox]) -> CaptureQuality:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image

    # Measure focus on the text region only. Empty background would otherwise
    # dominate and make every photograph look sharp.
    if boxes:
        xs = [b.bbox[0] for b in boxes]
        ys = [b.bbox[1] for b in boxes]
        xe = [b.bbox[0] + b.bbox[2] for b in boxes]
        ye = [b.bbox[1] + b.bbox[3] for b in boxes]
        region = gray[max(0, min(ys)):min(gray.shape[0], max(ye)),
                      max(0, min(xs)):min(gray.shape[1], max(xe))]
        if region.size == 0:
            region = gray
    else:
        region = gray

    focus = soft_edge_fraction(region)
    contrast = float(np.percentile(region, 95) - np.percentile(region, 5))
    confidence = float(np.mean([b.confidence for b in boxes])) if boxes else 0.0
    resolution = int(min(image.shape[:2]))

    notes: list[str] = []
    grade = "good"

    if resolution < MIN_RESOLUTION:
        grade = "poor"
        notes.append(f"Image is only {resolution} px on its short side; "
                     f"at least {MIN_RESOLUTION} px is needed.")

    if focus >= FOCUS_POOR:
        grade = "poor"
        notes.append("Image is badly out of focus.")
    elif focus >= FOCUS_MARGINAL and grade != "poor":
        grade = "marginal"
        notes.append("Image is slightly soft; hold steadier or move closer.")

    if len(boxes) < 3:
        grade = "poor"
        notes.append("Almost no text could be read from this image.")
    elif confidence < CONF_POOR:
        grade = "poor"
        notes.append(f"Text recognition confidence is low ({confidence:.0%}).")
    elif confidence < CONF_MARGINAL and grade == "good":
        grade = "marginal"
        notes.append(f"Text recognition confidence is moderate ({confidence:.0%}).")

    if contrast < 40:
        grade = "poor"
        notes.append("Not enough contrast between the print and the background.")

    if not notes:
        notes.append("Capture quality is good.")

    return CaptureQuality(
        focus=round(focus, 4),
        contrast=round(contrast, 1),
        ocr_confidence=round(confidence, 4),
        text_count=len(boxes),
        resolution_px=resolution,
        grade=grade,
        notes=" ".join(notes),
    )
