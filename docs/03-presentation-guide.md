# SIH26034 — Presentation Guide

**Everything to put on the slides, plus what to say out loud**

Companion to `02-project-roadmap.md`. Use this to fill in the official SIH idea-submission template.

---

## Before you start

1. **Download the official template from sih.gov.in.** Do not use a template from a blog or a YouTube description. The official one has fixed headings and judges expect them.
2. The idea submission is uploaded as a **PDF**.
3. Judges score: *novelty, complexity, clarity and detail in the prescribed format, feasibility, practicability, sustainability, scale of impact, user experience, potential for future work.* Every slide below is written to hit one or more of these.

The official template historically has **five content slides**, with your PS ID and team details in a header band on each. The content below maps to those five. If this year's template differs, the content still fits — just move it into the boxes provided.

---

## The one sentence everything hangs off

> **"The law says the MRP must be printed at least 2.5 millimetres tall. Nobody can check that with their eyes. We built software that measures it from a photograph."**

Open with this. Close with this. If a judge remembers one thing, make it this.

---

## Slide 1 — Proposed Solution

*Template headings usually: Detailed explanation of the proposed solution · How it addresses the problem · Innovation and uniqueness*

### Put on the slide

**Title:** `Naap-Tol: Measuring Legal Metrology Compliance, Not Just Reading It`

*(Alternative names: PackCheck · MAAP-Check · Metro-Scan. Pick one and use it everywhere.)*

**Detailed explanation — 3 lines maximum**

> Photograph a packet alongside a small printed reference card. The system reads all mandatory declarations, **measures letter heights in millimetres**, checks them against the Legal Metrology (Packaged Commodities) Rules, 2011, and issues a rule-by-rule compliance report card with the exact citation for every failure.

**How it addresses the problem**

- Inspectors check packets by hand with a ruler — a few dozen a day, subjectively
- Our system checks one in seconds, objectively, with reproducible evidence
- Output is a signed PDF an officer can attach to a case file

**Innovation and uniqueness — 3 bullets, and make them count**

| | |
|---|---|
| **1. We measure, we don't just read** | Rule 7 sets minimum letter heights of 1.0–6.0 mm based on panel area. A reference marker of known size gives us millimetres-per-pixel. Text extraction alone cannot detect this violation — and it is one of the most common. |
| **2. We never guess a violation** | Blurry photo, missing marker or a borderline measurement returns **NEEDS PHYSICAL CHECK**, not FAIL. A wrong accusation against a shopkeeper is worse than no answer. |
| **3. Rules live in a file, not in the code** | The Rules were amended in 2021, 2022, 2023, 2025 and 2026. Ours are stored as editable JSON with valid-from dates, so an officer updates a file instead of a developer rewriting software. |

### The visual for this slide

Draw the report card mock-up from the roadmap document. Green ticks, red crosses, one amber. Include a red cross that reads:

```
❌ Rule 7(2) — Letter height 2.1 mm
   Required: 2.5 mm (panel area 240 cm²)
```

That single line does more work than any paragraph.

### Say out loud

> "Every packet you buy must legally print nine things. Most people know that. What almost nobody knows is that the law also says how *tall* those letters have to be — down to the millimetre. A company can print everything correctly and still be breaking the law because the text is two-point-one millimetres instead of two-point-five. You cannot see that. An inspector with a ruler struggles to see it. A camera can measure it exactly. That's what we built."

---

## Slide 2 — Technical Approach

*Template headings usually: Technologies to be used · Methodology and process for implementation*

### Technologies — show as logos in a row, not a list

| Purpose | Tool |
|---|---|
| Language | Python |
| Web app | Streamlit |
| Text recognition | EasyOCR / PaddleOCR (English + Hindi) |
| Image processing & measurement | OpenCV — ArUco markers |
| Rules | JSON rule pack, version-controlled |
| Data | SQLite |
| Charts | Plotly |
| Reports | fpdf2 |

All open-source. All free. Say that.

### The process flow — draw this yourself

```
 ┌──────────┐   ┌───────────┐   ┌────────────┐   ┌──────────┐   ┌─────────┐
 │  CAPTURE │──►│ RECTIFY & │──►│  EXTRACT   │──►│  RULE    │──►│ REPORT  │
 │ photo +  │   │  MEASURE  │   │ 9 declara- │   │  ENGINE  │   │  CARD   │
 │ ArUco    │   │ mm/pixel  │   │ tions      │   │ 12 rules │   │ + PDF   │
 │ card     │   │ scale     │   │ via OCR    │   │ + cites  │   │         │
 └──────────┘   └───────────┘   └────────────┘   └──────────┘   └─────────┘
                                                        │
                                                        ▼
                                            PASS / FAIL / NOT APPLICABLE /
                                            NEEDS PHYSICAL CHECK
```

### The measurement explainer — this deserves its own box

Judges will ask. Pre-empt them:

```
   ArUco card = 50 mm, measures 200 px in photo
                    ↓
            1 pixel = 0.25 mm
                    ↓
     "MRP ₹40" text box = 9 px tall
                    ↓
        Letter height = 2.25 mm
                    ↓
   Rule 7 requires 2.5 mm → NON-COMPLIANT
```

Five boxes. Anyone can follow it. This is the most persuasive object in your whole deck.

### Say out loud

> "The measurement works like this. We put a card of known size — exactly fifty millimetres — in the same photograph. OpenCV finds it and tells us it's two hundred pixels wide. So one pixel is a quarter of a millimetre. Now when the text detector gives us a box around the MRP that's nine pixels tall, we know that's 2.25 millimetres. The rule requires 2.5. That's a violation, and we can prove it."

---

## Slide 3 — Feasibility and Viability

*Template headings usually: Analysis of feasibility · Potential challenges and risks · Strategies for overcoming them*

### Feasibility — lead with proof, not promises

- **Working prototype already running** — insert your screenshot here
- Every component is a mature open-source library; nothing needs to be invented
- Tested on **40 real retail packets** collected from local shops
- Measurement accuracy **±0.2 mm**, verified against 20 labels measured by hand

> Put your real numbers here, whatever they turn out to be. A modest honest number beats an impressive invented one, because judges probe. Update this slide the day before you submit.

### Challenges and how you handle them — use a two-column table

| Challenge | Our strategy |
|---|---|
| Curved bottles and tins distort text | Detect pack shape; apply cylindrical correction; guide the user to capture the flat centre panel |
| Shiny, metallised or crumpled wrappers | Capture guidance in the app (angle, no flash glare); allow multiple shots and merge results |
| OCR misreads characters | Every reading shown next to its cropped image so an officer verifies in one glance; officer confirms before any action |
| Photo tilted or blurred, marker missing | Return NEEDS PHYSICAL CHECK rather than a verdict — we never manufacture a violation |
| Rules keep changing | Rules stored as JSON with valid-from/valid-to dates; judge each pack by the rules in force when it was packed |
| Hindi and regional scripts | OCR configured for Devanagari; the law permits English or Hindi |

That NEEDS PHYSICAL CHECK row is the one a ministry judge will remember. Do not cut it for space.

### Say out loud

> "We were careful about one thing above all. This is a government enforcement tool. If it wrongly flags an honest shopkeeper, it does more harm than good. So when the system isn't confident — bad photo, missing marker, a measurement sitting right on the borderline — it does not say violation. It says 'needs physical check' and hands it to a human. We'd rather miss a case than create a false one."

---

## Slide 4 — Impact and Benefits

*Template headings usually: Potential impact on target audience · Benefits (social, economic, environmental)*

### Who benefits — four columns with icons

| 👮 **Inspectors** | 🏭 **Manufacturers** | 🛒 **Consumers** | 🏛️ **Ministry** |
|---|---|---|---|
| Check in seconds, not minutes | Catch errors before printing lakhs of wrappers | Scan before buying; report with evidence | National compliance picture |
| Objective, reproducible evidence | Avoid seizure and rework costs | Know their rights | Target inspections where violations cluster |
| Court-ready PDF report | Stay current as rules change | | Audit online listings at scale |

### The benefits

**Social** — Consumers get the information the law promises them. Enforcement becomes consistent instead of depending on which inspector visits.

**Economic** — Under Section 36 of the Legal Metrology Act, penalties run **₹25,000 → ₹50,000 → ₹1,00,000 plus up to one year's imprisonment** for repeat offences. Prevention is far cheaper than prosecution, for both government and industry. Rework of misprinted packaging costs manufacturers lakhs per SKU.

**Environmental** — Catching label errors *before* printing avoids scrapping and reprinting entire runs of packaging material.

**Scale** — India has millions of retail outlets and crores of online product listings. The 2026 amendment adds new country-of-origin and net-quantity duties for e-commerce listings, with a transition running to July 2027. Manual checking cannot reach this. Software can.

### Say out loud

> "There are lakhs of shops and a few thousand inspectors. The arithmetic just doesn't work. This doesn't replace an inspector — it tells them which shop to walk into, and hands them the evidence when they get there."

---

## Slide 5 — Research and References

*Template headings usually: Details and links of reference and research work*

### What to list

- **Legal Metrology (Packaged Commodities) Rules, 2011** — Rules 6, 7, 9, 11, 13, 24, 26
- **Legal Metrology Act, 2009** — Section 36, penalties
- **Amendment Rules 2025** (notified 29 Oct 2025) — medical device labelling harmonisation
- **Amendment Rules 2026** — e-commerce country-of-origin and net-quantity disclosure
- **eMaap** — the Department of Consumer Affairs' National Legal Metrology Portal, which our reports are designed to integrate with
- **OpenCV ArUco** documentation — marker-based scale recovery
- **EasyOCR / PaddleOCR** — multilingual text recognition
- **Our own field study** — 40 retail packets photographed and 20 hand-measured

### Also put here: what exists already, and why yours is different

Judges specifically reward knowing the landscape.

> Existing barcode and QR scanner apps identify a product. FSSAI and consumer apps display product information. **None of them verify compliance, and none measure printed letter height.** Our system is the first to treat this as a measurement problem rather than a text-reading problem.

### And a short future-scope line

> Next: online listing compliance checks under the 2026 amendment; pre-print artwork verification for manufacturers, where vector PDF files allow exact measurement with zero estimation error; and a national violation dashboard for targeting inspections.

---

## Design rules for the deck

1. **Draw your own diagrams.** Judges spot stock images instantly. Hand-drawn-then-digitised is fine and often better.
2. **Screenshot of working code beats any mockup.** Even if it's ugly. Label it "working prototype, [date]".
3. **Six lines of text per slide, maximum.** If you need more, you need a diagram.
4. **No robot or glowing-brain images.** No blockchain. No "revolutionary" or "game-changing."
5. **Fill every box in the template.** Empty space reads as an incomplete submission, and "clarity and details in the prescribed format" is an explicit scoring criterion.
6. **One colour accent, one font.** Consistency looks more professional than variety.
7. **Check the PS ID reads `SIH26034`** on every slide it appears.

---

## For the live presentation (internal hackathon and finale)

### Timing — assume 5 to 8 minutes

| Minutes | What |
|---|---|
| 0:00–0:45 | The hook: the millimetre story |
| 0:45–1:30 | Who's affected and why manual checking can't scale |
| 1:30–3:30 | **Live demo** — photograph a real packet, show the report card |
| 3:30–4:30 | How the measurement works (the five-box diagram) |
| 4:30–5:30 | Accuracy numbers, and how you avoid false accusations |
| 5:30–6:30 | Impact and future scope |
| 6:30+ | Questions |

### Demo rules

- **Record a backup video.** Venue wifi will fail. It always fails.
- Demo on a packet that **actually fails a rule** — a pass is boring
- Have the packet physically in your hand to show the judges
- Rehearse the demo ten times. Ten. The demo is where teams win or lose.

### Handling a question you can't answer

Say: *"We haven't tested that yet — it's on our list."* Then move on.

Judges respect that far more than a bluff. Bluffing invites a follow-up question, and the follow-up is where teams fall apart.

---

## Content checklist before submitting

- [ ] PS ID is exactly `SIH26034` everywhere
- [ ] Official template used, every box filled
- [ ] The word **"millimetre"** appears on at least two slides
- [ ] NEEDS PHYSICAL CHECK / no-false-accusation point is present
- [ ] Rule numbers cited (Rule 6, Rule 7 Table-I, Section 36)
- [ ] At least one screenshot of your own working code
- [ ] All diagrams drawn by your team
- [ ] Six team members listed, roles shown
- [ ] Exported to PDF, opens correctly, fonts not broken
- [ ] Someone outside the team has read it and understood it
- [ ] Submitted **two days before** the deadline

---

## Sources

- [Legal Metrology (Packaged Commodities) Rules, 2011](https://legalmetrologymh.in/public/temp/368/02d3c4fef3045bc21d90ba000a28357e.pdf)
- [Rule 6 — Declarations on every package](https://indiankanoon.org/doc/38209662/)
- [Section 36, Legal Metrology Act 2009](https://lawgist.in/legal-metrology-act/36)
- [PIB — Amendment Rules 2025](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2183777&reg=48&lang=2)
- [Amendment Rules 2026 — e-commerce disclosure](https://www.mondaq.com/india/dodd-frank-consumer-protection-act/1806934/legal-metrology-packaged-commodities-amendment-rules-2026-enhancing-transparency-and-consumer-protection-in-e-commerce)
- [PIB — eMaap National Legal Metrology Portal](https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2080446)
- [SIH 2026 guidelines — judging criteria and team rules](https://sih-uit.vercel.app/assets/sih-2026-guidelines.pdf)
