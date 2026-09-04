# SIH26034 — Naap-Tol

**Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels.**

Smart India Hackathon 2026 · Ministry of Consumer Affairs, Food & Public Distribution
Theme: Agriculture, FoodTech & Rural Development · Track: Software

---

## The idea in one sentence

Photograph a packet next to a small printed reference card. The system reads all nine mandatory declarations, **measures the printed letter heights in millimetres**, checks them against the 2011 Rules, and issues a rule-by-rule report card citing the exact rule behind every failure.

## Why this is not an OCR project

Rule 7 of the LMPC Rules sets **minimum letter heights of 1.0–6.0 mm**, keyed to the computed area of the pack's principal display panel. A label reader can tell you the MRP is printed. It cannot tell you the MRP is printed 0.4 mm too small — and that under-height printing is itself an offence.

The law is a measurement law. So the system measures.

## Repository layout

```
topic/      Hackathon problem statement and reference material
docs/       Analysis, roadmap and presentation material
src/        Application source code
tests/      Unit and integration tests
config/     Configuration files and rule packs
scripts/    Utility and automation scripts
data/       Sample and test data
assets/     Images, diagrams, UI assets
```

## Documents

| File | What it is |
|---|---|
| [`docs/01-problem-analysis.md`](docs/01-problem-analysis.md) | Deep technical analysis — the full legal surface, users, reference architecture, differentiators and risks |
| [`docs/02-project-roadmap.md`](docs/02-project-roadmap.md) | **Start here.** What actually needs to be done, week by week, scoped for a first-year team |
| [`docs/03-presentation-guide.md`](docs/03-presentation-guide.md) | Slide-by-slide content, speaker notes and judge Q&A preparation |
| [`docs/SIH26034-Idea-Submission.pptx`](docs/SIH26034-Idea-Submission.pptx) | Editable 6-slide idea-submission deck |

## Planned stack

Python · Streamlit · EasyOCR / PaddleOCR (English + Hindi) · OpenCV (ArUco markers) · SQLite · Plotly · fpdf2

All open-source. No paid APIs. Runs on a laptop.

## How the measurement works

```
ArUco card is exactly 50 mm  →  measures 200 px in the photo
                             →  1 pixel = 0.25 mm
"MRP Rs.40" text box = 9 px  →  letter height = 2.25 mm
Rule 7 requires 2.5 mm       →  NON-COMPLIANT
```

When the scale cannot be recovered — blurred photo, missing marker, borderline reading — the system returns **NEEDS PHYSICAL CHECK**, never a verdict. It does not manufacture violations.

## Status

Planning and documentation. Implementation not yet started.

## Verify before relying on dates

Deadlines quoted in third-party sources conflict. Confirm the idea-submission deadline, the official PPT template and the full problem statement text on **sih.gov.in** before planning around them.
