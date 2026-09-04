# Running the Demo

**SIH26034 — Naap-Tol.** From a fresh laptop to a working demo in about ten minutes.

---

## 1. Install

```bash
git clone https://github.com/pranay9th/SIHP2026.git
cd SIHP2026
pip install -r requirements.txt
```

Then install Tesseract, which is a system program rather than a Python package:

| OS | Command |
|---|---|
| Ubuntu / Debian | `sudo apt install tesseract-ocr tesseract-ocr-hin` |
| macOS | `brew install tesseract tesseract-lang` |
| Windows | Installer at <https://github.com/UB-Mannheim/tesseract/wiki> — tick "Additional language data" for Hindi |

Check it:

```bash
tesseract --version
```

---

## 2. Generate the test labels and the reference card

```bash
python scripts/make_sample_labels.py
```

This writes five synthetic labels to `data/samples/`, each rendered at a known DPI so the true letter height of every declaration is known exactly, and a printable marker to `assets/aruco-reference-card-50mm.png`.

| Label | What it demonstrates |
|---|---|
| `compliant_biscuits` | A fully compliant pack — the control |
| `undersize_letters` | Letters 1.86 mm where Rule 7 requires 2.5 mm |
| `missing_tax_wording` | MRP printed without "inclusive of all taxes" |
| `wrong_unit_and_qualifier` | "approx. 1500 g" — a qualifier, a wrong unit, and bad price rounding |
| `imported_no_origin` | An import with no country of origin |

### Printing the reference card

Print `assets/aruco-reference-card-50mm.png` at **100 % scale** — not "fit to page", which silently resizes it. Measure the printed square with a ruler: it must be **exactly 50 mm** on each side. Every measurement the system makes depends on this one number, so check it rather than assuming.

---

## 3. Fill the dashboard

```bash
python scripts/seed_demo_data.py
```

Writes 30 real scans across brands, states and districts, so the dashboard opens with something in it. An empty dashboard makes a working system look unfinished.

---

## 4. Check it works

```bash
python -m pytest tests/ -q
```

Expect **53 passed**.

```bash
python scripts/benchmark.py --robustness
```

This prints the numbers for your slide.

---

## 5. Run the app

```bash
streamlit run app.py
```

Opens at <http://localhost:8501>.

---

## The numbers this produces

On the synthetic label set, with the clean-capture measurement chain:

| Metric | Result |
|---|---|
| Scale recovery error | **0.056 %** |
| Letter-height mean absolute error | **0.002 mm** |
| End-to-end verdict accuracy | **5 / 5** |
| Degraded-capture false accusations | **0** |

### Read this before you quote those numbers

These measure the **measurement chain** — marker detection, millimetres per pixel, ink-tight box, conversion to millimetres — on **clean synthetic renders**. They do not measure real-world capture, where lighting, curvature, print quality, glare and camera optics all add error.

So the honest framing is:

> "On synthetic labels with known ground truth, our measurement chain is accurate to 0.002 mm, which shows the geometry is right. On real photographs measured against a vernier caliper, our error is **X mm** — that is the number that says whether the product works."

**Go and produce X.** Photograph 20 real packets, measure the MRP letter height on each with a caliper, and compare. It is an afternoon's work and it is the difference between a claim and a result. A judge who asks "how do you know?" is asking for X, not for the synthetic figure.

---

## Demo script — five minutes

**0:00 The hook.** Hold up a real biscuit packet.
> "The law says the MRP on this packet must be printed at least two and a half millimetres tall. Nobody can check that by eye. An inspector with a ruler struggles. We measure it from a photograph."

**0:45 Show the compliant label.** Sample `compliant_biscuits`. Point at the sidebar: panel 108 cm², so Rule 7 requires 2.5 mm. Report card is all green, measured 3.08 mm.

**1:30 Show the violation.** Switch to `undersize_letters`. Same panel size, but the verdict flips to NON-COMPLIANT with:
> `Rule 7(2), Table-I — mrp letter height is 1.86 +/- 0.06 mm, below the 2.5 mm required for a 108 cm2 principal display panel.`
>
> "No OCR system can find that violation, because the text is printed perfectly. It is just too small. That is the offence."

**2:30 Show the other failure types.** `wrong_unit_and_qualifier` catches four separate breaches at once — the word "approx.", grams where kilograms are required, missing tax wording, and a price that is not rounded to the nearest 50 paise.

**3:15 Show the honesty.** Tick "Show rules that do not apply", or set net quantity to 8 g:
> "Under Rule 26 a sachet of ten grams or less is exempt, so every rule turns to NOT APPLICABLE rather than failing. And when the photo is too poor to be sure, the system returns NEEDS PHYSICAL CHECK instead of a violation. We would rather miss a case than accuse an honest shopkeeper."

**4:00 The evidence and the dashboard.** Download the PDF — show the rule-pack version, the image hash, the scale method and the uncertainty. Then the dashboard: most-breached rules, repeat offenders, the Section 36 escalation ladder.

**4:45 Close.**
> "Lakhs of shops, a few thousand inspectors. This does not replace an inspector. It tells them which shop to walk into and hands them the evidence when they get there."

### Demo rules

- **Record a backup video.** Venue wifi fails. It always fails.
- Rehearse ten times. The demo is where teams win or lose.
- Have the physical packet and the printed card in your hand.
- If something breaks, say what broke and move on. Do not debug in front of judges.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `No OCR backend available` | Tesseract is not installed or not on PATH. `tesseract --version` should work in the same terminal. |
| `No ArUco reference marker found` | The card is not in frame, is too small (needs 40+ px across), or was printed too faintly. Move closer. |
| Measurements look 5–10 % too large | The card was not printed at exactly 50 mm, or is not lying in the same plane as the label. Both matter. |
| Everything returns NEEDS PHYSICAL CHECK | Capture quality is being graded poor. Check the warning text under the verdict — usually focus or lighting. |
| Streamlit port already in use | `streamlit run app.py --server.port 8502` |
| Hindi text not read | Install the Hindi language data (`tesseract-ocr-hin`), or `pip install easyocr` and pick easyocr in the sidebar. |
