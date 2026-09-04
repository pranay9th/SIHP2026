"""Measure how accurate the measurement chain is, against known ground truth.

This is the script that produces the millimetre error figure for your slide.
Run it after scripts/make_sample_labels.py:

    python scripts/benchmark.py

IMPORTANT, and say this to the judges: this benchmarks the MEASUREMENT CHAIN
(marker detection -> mm-per-pixel -> ink-tight box -> millimetres) on clean
synthetic renders. It does not benchmark real-world capture, where lighting,
tilt, curvature, print quality and camera optics all add error. Photograph real
packs, measure them with a vernier caliper, and quote that number too. The
synthetic figure tells you the maths is right; only the caliper figure tells
you the product works.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from naaptol import extract as extract_mod  # noqa: E402
from naaptol import ocr as ocr_mod          # noqa: E402
from naaptol import pipeline, scale as scale_mod  # noqa: E402
from naaptol.models import PackageContext   # noqa: E402


def net_qty_g_ml(truth: dict) -> float | None:
    for line in truth["lines"]:
        text = line["text"].lower()
        if "net" in text and line.get("digits"):
            try:
                value = float(line["digits"].replace(",", ""))
            except ValueError:
                return None
            if " kg" in text:
                return value * 1000
            if re_has(text, " l") and " ml" not in text:
                return value * 1000
            return value
    return None


def re_has(text: str, token: str) -> bool:
    return token in text


def degrade(image, tilt: float = 0.0, blur: int = 0, noise: int = 0):
    """Simulate a hand-held photograph: perspective tilt, defocus, sensor noise."""
    import numpy as np

    out = image
    if tilt > 0:
        h, w = out.shape[:2]
        dx = w * tilt
        src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        dst = np.float32([[dx, tilt * h * 0.4], [w - dx * 0.3, 0],
                          [w, h - tilt * h * 0.3], [dx * 0.5, h]])
        matrix = cv2.getPerspectiveTransform(src, dst)
        out = cv2.warpPerspective(out, matrix, (w, h),
                                  borderValue=(238, 238, 234))
    if blur > 0:
        k = blur * 2 + 1
        out = cv2.GaussianBlur(out, (k, k), 0)
    if noise > 0:
        rng = np.random.default_rng(7)
        out = np.clip(out.astype(np.int16) +
                      rng.normal(0, noise, out.shape).astype(np.int16), 0, 255
                      ).astype(np.uint8)
    return out


def robustness_check(sample_dir: Path, manifest: list[dict], backend) -> None:
    """Show what the system does as capture quality falls apart.

    The point is not that it stays accurate. It will not. The point is that it
    degrades into INDETERMINATE rather than into confident wrong answers.
    """
    print("\n" + "=" * 60)
    print("DEGRADED CAPTURE BEHAVIOUR")
    print("=" * 60)
    print("  What happens as the photo gets worse. The goal is that bad input")
    print("  produces NEEDS PHYSICAL CHECK, never a confident false accusation.\n")

    conditions = [
        ("clean",            dict()),
        ("slight tilt",      dict(tilt=0.02)),
        ("strong tilt",      dict(tilt=0.08)),
        ("defocused",        dict(blur=3)),
        ("tilt + blur + noise", dict(tilt=0.05, blur=2, noise=12)),
        ("very blurred",     dict(blur=9)),
    ]

    truth = manifest[0]
    image = cv2.imread(str(sample_dir / f"{truth['name']}.png"))
    ctx = PackageContext(package_type="retail",
                         pdp_area_cm2=truth["pdp_area_cm2"],
                         net_quantity_g_or_ml=200)

    print(f"  {'condition':22s} {'scale grade':14s} {'height verdict':16s} overall")
    print("  " + "-" * 74)
    for name, kwargs in conditions:
        shot = degrade(image, **kwargs)
        result = pipeline.scan(shot, ctx, backend=backend)
        height = next(
            (f for f in result.findings if f.rule_id == "LMPC.R7.2.letter_height"),
            None,
        )
        print(f"  {name:22s} {result.scale.grade:14s} "
              f"{(height.verdict if height else 'n/a'):16s} {result.overall}")

    print("\n  A row that reads FAIL on a degraded shot would be a bug worth fixing")
    print("  before the demo. INDETERMINATE on a bad shot is the correct answer.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", default=str(ROOT / "data" / "samples"))
    parser.add_argument("--backend", default="auto")
    parser.add_argument("--robustness", action="store_true",
                        help="also report behaviour on degraded photographs")
    args = parser.parse_args()

    sample_dir = Path(args.samples)
    manifest_path = sample_dir / "manifest.json"
    if not manifest_path.exists():
        print("No samples found. Run scripts/make_sample_labels.py first.")
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    backend = ocr_mod.get_backend(args.backend)
    print(f"OCR backend: {backend.name}\n")

    scale_errors_pct: list[float] = []
    height_errors_mm: list[float] = []
    verdict_hits = 0
    rows = []

    for truth in manifest:
        image_path = sample_dir / f"{truth['name']}.png"
        image = cv2.imread(str(image_path))

        # --- scale accuracy ---------------------------------------------
        est = scale_mod.estimate(image)
        if est.usable:
            err_pct = abs(est.mm_per_px - truth["true_mm_per_px"]) / truth["true_mm_per_px"] * 100
            scale_errors_pct.append(err_pct)
        else:
            err_pct = float("nan")

        # --- measurement accuracy ---------------------------------------
        boxes = ocr_mod.read_text(image, backend=backend)
        facts = extract_mod.extract(boxes)
        measured_mm = None
        if est.usable and facts.measured_boxes:
            heights = [
                box.height_px * est.mm_per_px for box in facts.measured_boxes.values()
            ]
            measured_mm = min(heights)
            height_errors_mm.append(abs(measured_mm - truth["true_declaration_numeral_mm"]))

        # --- end-to-end verdict -----------------------------------------
        ctx = PackageContext(
            package_type="retail",
            pdp_area_cm2=truth["pdp_area_cm2"],
            is_imported="imported" in truth["name"],
            net_quantity_g_or_ml=net_qty_g_ml(truth),
        )
        result = pipeline.scan(image, ctx, backend=backend)
        correct = result.overall == truth["expect"]
        verdict_hits += int(correct)

        rows.append({
            "name": truth["name"],
            "scale_err_pct": err_pct,
            "true_mm": truth["true_declaration_numeral_mm"],
            "measured_mm": measured_mm,
            "expected": truth["expect"],
            "actual": result.overall,
            "correct": correct,
        })

    # --- report ----------------------------------------------------------
    print(f"{'label':30s} {'scale err':>10s} {'true mm':>9s} {'meas mm':>9s} "
          f"{'err mm':>8s}  {'expected':<22s} {'actual':<22s} ok")
    print("-" * 128)
    for r in rows:
        err = (abs(r["measured_mm"] - r["true_mm"]) if r["measured_mm"] else float("nan"))
        meas = f"{r['measured_mm']:.3f}" if r["measured_mm"] else "  n/a"
        print(f"{r['name']:30s} {r['scale_err_pct']:9.3f}% {r['true_mm']:9.3f} "
              f"{meas:>9s} {err:8.3f}  {r['expected']:<22s} {r['actual']:<22s} "
              f"{'yes' if r['correct'] else 'NO'}")

    print("\n" + "=" * 60)
    print("MEASUREMENT CHAIN ACCURACY (synthetic renders, clean capture)")
    print("=" * 60)
    if scale_errors_pct:
        print(f"  Scale error          mean {statistics.mean(scale_errors_pct):.3f} %   "
              f"max {max(scale_errors_pct):.3f} %")
    if height_errors_mm:
        mae = statistics.mean(height_errors_mm)
        print(f"  Letter height MAE    {mae:.3f} mm   max {max(height_errors_mm):.3f} mm")
    print(f"  End-to-end verdict   {verdict_hits}/{len(rows)} correct")
    print()
    print("  Quote this as: measurement-chain accuracy on synthetic labels.")
    print("  Then quote a SEPARATE figure from real photographs measured with")
    print("  a vernier caliper. Judges will ask which one you are quoting.")

    if args.robustness:
        robustness_check(sample_dir, manifest, backend)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
