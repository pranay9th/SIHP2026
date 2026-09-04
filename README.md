# SIH26034 — Naap-Tol

**Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels.**

Smart India Hackathon 2026 · Ministry of Consumer Affairs, Food & Public Distribution
Theme: Agriculture, FoodTech & Rural Development · Track: Software

---

## The idea in one sentence

Photograph a packet next to a small printed reference card. The system reads all nine mandatory declarations, **measures the printed letter heights in millimetres**, checks them against the 2011 Rules, and issues a rule-by-rule report card citing the exact rule behind every failure.

## Why this is not an OCR project

Rule 7 sets **minimum letter heights of 1.0–6.0 mm**, keyed to the computed area of the pack's principal display panel. A label reader can tell you the MRP is printed. It cannot tell you the MRP is printed 0.4 mm too small — and that under-height printing is itself an offence.

The law is a measurement law. So the system measures.

## Quick start

```bash
pip install -r requirements.txt
# plus Tesseract: sudo apt install tesseract-ocr   (see docs/05-running-the-demo.md)

python scripts/make_sample_labels.py   # test labels + printable reference card
python scripts/seed_demo_data.py       # fill the dashboard
python -m pytest tests/ -q             # 53 tests
python scripts/benchmark.py --robustness
streamlit run app.py
```

## What works today

| | |
|---|---|
| **Marker-based rectification** | Flattens a hand-held photograph on the ArUco card, removing the ~7 % height error a 5° tilt introduces |
| **Millimetre measurement** | Ink-tight glyph boxes located at the half-maximum edge, so the reading survives defocus |
| **14 encoded rules** | Rule 6(1) declarations, Rule 7 letter height and width, Rules 11 and 13 quantity and units, Rule 9(4) language, Rule 26 exemptions |
| **Five verdicts** | PASS · FAIL · NOT_APPLICABLE · BORDERLINE · INDETERMINATE |
| **Capture-quality gate** | A poor photograph cannot produce a FAIL, only a NEEDS PHYSICAL CHECK |
| **Temporal rule versioning** | Judges a pack by the rules in force on its date of packing |
| **Evidence PDF** | Rule-pack version, image SHA-256, scale method, measurement uncertainty |
| **Enforcement dashboard** | Most-breached rules, repeat offenders, Section 36 escalation ladder |
| **Synthetic label generator** | Labels with exactly known mm heights, for ground-truth benchmarking |

## Measured results

On synthetic labels with known ground truth:

| Metric | Result |
|---|---|
| Scale recovery error | 0.056 % |
| Letter-height mean absolute error | 0.002 mm |
| End-to-end verdict accuracy | 5 / 5 |
| False accusations on degraded photographs | 0 |

**These measure the measurement chain on clean renders, not real-world capture.** Photograph real packs, measure them with a vernier caliper, and quote that figure alongside. See `docs/05-running-the-demo.md`.

## How the measurement works

```
ArUco card is exactly 50 mm  →  detected, image rectified on its corners
                             →  1 px = 0.0833 mm in the flattened plane
"MRP Rs.40.00" glyph box     →  37 px tall at the half-maximum edge
                             →  letter height = 3.08 mm
Panel is 108 cm2             →  Rule 7 Table-I requires 2.5 mm  →  PASS
```

When the marker is missing, the panel area is unknown, the scale is only indicative, or the photograph is too poor, the system returns **INDETERMINATE**. It never manufactures a violation.

## Repository layout

```
topic/      Problem statement
docs/       Analysis, roadmap, presentation, licensing, demo guide
src/        naaptol package
tests/      53 tests
config/     rules/lmpc-2011.json - the rule pack
scripts/    label generator, benchmark, demo seeder, git push helper
data/       Generated samples and the scan database
assets/     Printable reference card
app.py      Streamlit application
```

## Documents

| File | What it is |
|---|---|
| [`docs/01-problem-analysis.md`](docs/01-problem-analysis.md) | Deep technical analysis — legal surface, users, architecture, risks |
| [`docs/02-project-roadmap.md`](docs/02-project-roadmap.md) | **Start here.** What to do, week by week, scoped for a first-year team |
| [`docs/03-presentation-guide.md`](docs/03-presentation-guide.md) | Slide-by-slide content, speaker notes, judge Q&A |
| [`docs/04-licensing-and-tooling.md`](docs/04-licensing-and-tooling.md) | What must be purchased (nothing), licences, legal permissions |
| [`docs/05-running-the-demo.md`](docs/05-running-the-demo.md) | Setup, demo script, troubleshooting |
| [`docs/SIH26034-Idea-Submission.pptx`](docs/SIH26034-Idea-Submission.pptx) | Editable 6-slide idea-submission deck |

## Cost

**Zero.** Every component is open source — Apache 2.0, BSD, MIT, PSF or public domain. No paid API, no GPU, no cloud subscription, no vendor lock-in. Runs offline on a laptop, which matters because the officers who would use it work in markets without reliable connectivity. The only spend is about ₹5 to print the reference card.

## Status and honesty

Working prototype. It has been tested on synthetic labels, **not yet on real photographs of real packets** — that is the next and most important step.

The system is advisory. Every report carries: *"Decision support for a Legal Metrology officer, not an adjudication."* Verify against the bare Act and Rules before any enforcement action.

## Before relying on dates

Third-party sources disagree on the SIH idea-submission deadline (15 vs 20 September 2026). Confirm the deadline, the official PPT template and the full problem statement on **sih.gov.in**.
