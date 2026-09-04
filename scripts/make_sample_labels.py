"""Generate synthetic label images with EXACTLY known letter heights.

Why this exists: you cannot prove a measurement system works without ground
truth, and hand-measuring hundreds of real labels with a caliper is slow. Here
we render labels at a known DPI, so the true cap height of every declaration is
known to the micrometre, and place a 50 mm ArUco marker in the same frame.

Run it, then run scripts/benchmark.py to get a millimetre error figure you can
put on a slide.

    python scripts/make_sample_labels.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from naaptol import scale as scale_mod  # noqa: E402

DPI = 300
MM_PER_INCH = 25.4
MARKER_MM = 50.0

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def mm_to_px(mm: float, dpi: int = DPI) -> int:
    return int(round(mm / MM_PER_INCH * dpi))


def find_font_path() -> str:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    raise RuntimeError(
        "No TrueType font found. Install fonts-dejavu, or edit FONT_CANDIDATES."
    )


def font_for_cap_height_mm(font_path: str, cap_mm: float, dpi: int = DPI) -> ImageFont.FreeTypeFont:
    """Pick the point size whose CAP HEIGHT is cap_mm.

    Cap height, not the font's nominal size: Rule 7 is about the height of the
    printed character, and nominal point size includes ascender and descender
    space that never appears as ink.
    """
    target_px = mm_to_px(cap_mm, dpi)
    lo, hi = 4, 800
    best = ImageFont.truetype(font_path, 12)
    while lo <= hi:
        mid = (lo + hi) // 2
        font = ImageFont.truetype(font_path, mid)
        # "H" is a flat-topped, flat-bottomed capital: its ink box IS cap height.
        bbox = font.getbbox("H")
        cap_px = bbox[3] - bbox[1]
        if cap_px < target_px:
            lo, best = mid + 1, font
        elif cap_px > target_px:
            hi = mid - 1
        else:
            return font
    return best


def true_cap_height_mm(font: ImageFont.FreeTypeFont, dpi: int = DPI) -> float:
    bbox = font.getbbox("H")
    return (bbox[3] - bbox[1]) * MM_PER_INCH / dpi


def true_ink_height_mm(font: ImageFont.FreeTypeFont, text: str, dpi: int = DPI) -> float:
    """Ink height of a specific string, in millimetres.

    Needed because Rule 7 governs "any numeral and letter", and in most
    typefaces the digits are NOT the same height as the capitals. DejaVu Sans,
    for instance, draws digits about 6 % taller than cap height. Benchmarking a
    measured numeral against a cap-height ground truth would report a 6 % error
    that is really a definition mismatch, not a measurement fault.
    """
    bbox = font.getbbox(text)
    return (bbox[3] - bbox[1]) * MM_PER_INCH / dpi


def digits_in(text: str) -> str:
    """The numeral run a measurement rule would land on, e.g. '40.00'."""
    import re as _re
    runs = _re.findall(r"\d[\d.,]*", text)
    return max(runs, key=len) if runs else ""


# --------------------------------------------------------------------------
# Label specifications
# --------------------------------------------------------------------------

SPECS = [
    {
        "name": "compliant_biscuits",
        "panel_mm": (120, 90),          # 108 cm2 -> needs 2.5 mm
        "declaration_cap_mm": 3.0,
        "lines": [
            ("Crisp Salted Biscuits", 5.0),
            ("Manufactured by: Sunrise Foods Pvt Ltd,", 2.2),
            ("Plot 14, MIDC Industrial Area, Pune 411019", 2.2),
            ("Net Wt. 200 g", None),
            ("MRP Rs.40.00 (inclusive of all taxes)", None),
            ("Mfd: 03/2026    Best Before 9 months from packing", 2.2),
            ("Consumer care: care@sunrisefoods.in  1800 200 3040", 2.2),
        ],
        "expect": "COMPLIANT",
    },
    {
        "name": "undersize_letters",
        "panel_mm": (120, 90),          # 108 cm2 -> needs 2.5 mm
        "declaration_cap_mm": 1.9,      # deliberately below the threshold
        "lines": [
            ("Toffee Assorted Candy", 5.0),
            ("Manufactured by: Meethi Foods Ltd,", 2.2),
            ("22 Ring Road, Indore 452001", 2.2),
            ("Net Wt. 150 g", None),
            ("MRP Rs.25.00 (inclusive of all taxes)", None),
            ("Mfd: 01/2026", 2.2),
            ("Consumer care: help@meethi.in  1800 121 2121", 2.2),
        ],
        "expect": "NON-COMPLIANT",
    },
    {
        "name": "missing_tax_wording",
        "panel_mm": (150, 110),         # 165 cm2 -> needs 2.5 mm
        "declaration_cap_mm": 3.2,
        "lines": [
            ("Coconut Hair Oil", 5.0),
            ("Manufactured by: Kerala Naturals LLP,", 2.2),
            ("Survey 88, Alappuzha 688001", 2.2),
            ("Net Vol. 200 ml", None),
            ("MRP Rs.99.00", None),                # no "inclusive of all taxes"
            ("Mfd: 02/2026", 2.2),
            ("Consumer care: care@keralanaturals.in", 2.2),
        ],
        "expect": "NON-COMPLIANT",
    },
    {
        "name": "wrong_unit_and_qualifier",
        "panel_mm": (200, 140),         # 280 cm2 -> needs 2.5 mm
        "declaration_cap_mm": 3.5,
        "lines": [
            ("Premium Basmati Rice", 5.5),
            ("Packed by: Doaba Agro Mills,", 2.4),
            ("Grand Trunk Road, Karnal 132001", 2.4),
            ("Net Weight approx. 1500 g", None),   # qualifier + should be kg
            ("MRP Rs.249.75", None),               # bad rounding too
            ("Mfd: 12/2025", 2.4),
            ("Consumer care: 1800 313 1313", 2.4),
        ],
        "expect": "NON-COMPLIANT",
    },
    {
        "name": "imported_no_origin",
        "panel_mm": (90, 70),           # 63 cm2 -> needs 1.5 mm
        "declaration_cap_mm": 2.4,
        "lines": [
            ("Dark Chocolate Bar", 4.5),
            ("Imported by: Global Treats India Pvt Ltd,", 2.0),
            ("Andheri East, Mumbai 400069", 2.0),
            ("Net Wt. 80 g", None),
            ("MRP Rs.180.00 (inclusive of all taxes)", None),
            ("Mfd: 11/2025", 2.0),
            ("Consumer care: care@globaltreats.co.in", 2.0),
        ],
        "expect": "NON-COMPLIANT",     # country of origin missing
    },
]


def render_label(spec: dict, font_path: str, dpi: int = DPI) -> tuple[np.ndarray, dict]:
    """Render one label plus the reference marker. Returns image and ground truth."""
    panel_w_mm, panel_h_mm = spec["panel_mm"]
    margin_mm = 6.0
    marker_gap_mm = 8.0

    canvas_w_mm = panel_w_mm + marker_gap_mm + MARKER_MM + margin_mm * 2
    canvas_h_mm = max(panel_h_mm, MARKER_MM) + margin_mm * 2

    W, H = mm_to_px(canvas_w_mm, dpi), mm_to_px(canvas_h_mm, dpi)
    img = Image.new("RGB", (W, H), (238, 238, 234))
    draw = ImageDraw.Draw(img)

    # the pack panel
    px0, py0 = mm_to_px(margin_mm, dpi), mm_to_px(margin_mm, dpi)
    px1 = px0 + mm_to_px(panel_w_mm, dpi)
    py1 = py0 + mm_to_px(panel_h_mm, dpi)
    draw.rectangle([px0, py0, px1, py1], fill=(255, 255, 255), outline=(120, 120, 120), width=2)

    decl_mm = spec["declaration_cap_mm"]
    cursor_y = py0 + mm_to_px(4.0, dpi)
    pad_x = px0 + mm_to_px(4.0, dpi)
    truth_lines = []

    for text, cap_mm in spec["lines"]:
        size_mm = decl_mm if cap_mm is None else cap_mm
        font = font_for_cap_height_mm(font_path, size_mm, dpi)
        actual_mm = true_cap_height_mm(font, dpi)
        draw.text((pad_x, cursor_y), text, font=font, fill=(15, 15, 15))
        bbox = draw.textbbox((pad_x, cursor_y), text, font=font)
        digits = digits_in(text)
        truth_lines.append({
            "text": text,
            "requested_cap_mm": round(size_mm, 4),
            "true_cap_mm": round(actual_mm, 4),
            "digits": digits,
            "true_numeral_mm": round(true_ink_height_mm(font, digits, dpi), 4) if digits else None,
            "is_declaration": cap_mm is None,
            "bbox": [bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]],
        })
        cursor_y = bbox[3] + mm_to_px(1.6, dpi)

    # the reference marker, printed at exactly MARKER_MM
    marker_px = mm_to_px(MARKER_MM, dpi)
    marker = scale_mod.generate_marker(0, marker_px)
    marker_rgb = np.dstack([marker] * 3)
    mx = px1 + mm_to_px(marker_gap_mm, dpi)
    my = mm_to_px(margin_mm, dpi)
    img_np = np.array(img)
    img_np[my:my + marker_px, mx:mx + marker_px] = marker_rgb

    truth = {
        "name": spec["name"],
        "dpi": dpi,
        "true_mm_per_px": MM_PER_INCH / dpi,
        "marker_mm": MARKER_MM,
        "panel_mm": [panel_w_mm, panel_h_mm],
        "pdp_area_cm2": round(panel_w_mm * panel_h_mm / 100.0, 2),
        "declaration_cap_mm": round(decl_mm, 4),
        "true_declaration_cap_mm": round(
            next(l["true_cap_mm"] for l in truth_lines if l["is_declaration"]), 4
        ),
        # What a Rule 7 measurement will actually land on: the smallest numeral
        # run among the measured declarations. This is the benchmark target.
        "true_declaration_numeral_mm": round(min(
            l["true_numeral_mm"] for l in truth_lines
            if l["is_declaration"] and l["true_numeral_mm"]
        ), 4),
        "expect": spec["expect"],
        "lines": truth_lines,
    }
    return cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR), truth


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(ROOT / "data" / "samples"))
    parser.add_argument("--dpi", type=int, default=DPI)
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    font_path = find_font_path()

    manifest = []
    for spec in SPECS:
        image, truth = render_label(spec, font_path, args.dpi)
        img_path = out_dir / f"{spec['name']}.png"
        cv2.imwrite(str(img_path), image)
        (out_dir / f"{spec['name']}.truth.json").write_text(
            json.dumps(truth, indent=2), encoding="utf-8"
        )
        manifest.append(truth)
        print(f"  {img_path.name:32s} panel {truth['pdp_area_cm2']:>7.1f} cm2   "
              f"declaration cap height {truth['true_declaration_cap_mm']:.3f} mm   "
              f"expect {truth['expect']}")

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n{len(manifest)} labels written to {out_dir}")

    # Also drop a printable reference card.
    card = scale_mod.generate_marker(0, mm_to_px(MARKER_MM, args.dpi))
    card_path = ROOT / "assets" / "aruco-reference-card-50mm.png"
    card_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(card_path), card)
    print(f"Printable reference card: {card_path}  (print at exactly {MARKER_MM:.0f} mm)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
