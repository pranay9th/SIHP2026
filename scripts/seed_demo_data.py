"""Populate the dashboard with scans so the demo does not open empty.

An empty dashboard makes a working system look unfinished. This scans every
sample label several times under different brands, states and districts, so the
enforcement view has something real in it, produced by the real pipeline rather
than invented rows.

    python scripts/seed_demo_data.py
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from naaptol import ocr, pipeline, store  # noqa: E402
from naaptol.models import PackageContext  # noqa: E402

BRANDS = {
    "compliant_biscuits":       ("Sunrise Foods", "Crisp Salted Biscuits", "food"),
    "undersize_letters":        ("Meethi Foods", "Assorted Toffee", "confectionery"),
    "missing_tax_wording":      ("Kerala Naturals", "Coconut Hair Oil", "cosmetics"),
    "wrong_unit_and_qualifier": ("Doaba Agro Mills", "Basmati Rice", "staples"),
    "imported_no_origin":       ("Global Treats India", "Dark Chocolate Bar", "food"),
}

PLACES = [
    ("Maharashtra", "Pune"), ("Maharashtra", "Mumbai Suburban"),
    ("Madhya Pradesh", "Indore"), ("Kerala", "Alappuzha"),
    ("Haryana", "Karnal"), ("Delhi", "New Delhi"),
    ("Tamil Nadu", "Coimbatore"), ("Karnataka", "Bengaluru Urban"),
]

QTY = {
    "compliant_biscuits": 200, "undersize_letters": 150,
    "missing_tax_wording": 200, "wrong_unit_and_qualifier": 1500,
    "imported_no_origin": 80,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=6,
                        help="how many times to scan each sample")
    parser.add_argument("--db", default=None)
    parser.add_argument("--backend", default="auto")
    args = parser.parse_args()

    random.seed(11)
    sample_dir = ROOT / "data" / "samples"
    manifest_path = sample_dir / "manifest.json"
    if not manifest_path.exists():
        print("Run scripts/make_sample_labels.py first.")
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    backend = ocr.get_backend(args.backend)
    conn = store.connect(args.db)

    written = 0
    for truth in manifest:
        name = truth["name"]
        brand, product, category = BRANDS[name]
        image = cv2.imread(str(sample_dir / f"{name}.png"))
        image_bytes = (sample_dir / f"{name}.png").read_bytes()

        ctx = PackageContext(
            package_type="retail",
            pdp_area_cm2=truth["pdp_area_cm2"],
            is_imported=("imported" in name),
            net_quantity_g_or_ml=QTY[name],
        )
        # Scan once; the verdict is deterministic, so reuse it across places
        # rather than burning OCR time on identical images.
        result = pipeline.scan(image, ctx, backend=backend, image_bytes=image_bytes)

        for _ in range(args.repeats):
            state, district = random.choice(PLACES)
            store.save(conn, result, brand=brand, product=product,
                       category=category, state=state, district=district)
            written += 1
        print(f"  {name:28s} {result.overall:22s} x{args.repeats}")

    data = store.summary(conn)
    print(f"\n{written} scans written. Totals: {data['by_overall']}")
    print("Top breached rules:")
    for row in data["top_rules"][:5]:
        print(f"  {row['citation']:28s} {row['title'][:44]:46s} {row['n']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
