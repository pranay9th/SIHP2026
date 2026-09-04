# SIH26034 — Deep Dive Analysis

**Problem Statement:** Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels.

| Field | Value |
|---|---|
| PS ID | SIH26034 |
| Organisation | Ministry of Consumer Affairs, Food & Public Distribution (Department of Consumer Affairs) |
| Theme | Agriculture, FoodTech & Rural Development |
| Category | Software |
| Idea submission deadline | 20 September 2026 (per third-party PS catalogue — **verify on sih.gov.in**) |
| Document version | v1.0 — 04 Sep 2026 |

---

## 1. What the problem actually is

The one-line statement hides four separate problems. Reading it as "build an OCR app that reads labels" is the trap most teams will fall into, and it is the reason most submissions will look identical.

**1.1 The regulator's problem.** Legal Metrology is enforced by ~36 State/UT Legal Metrology departments. An Inspector physically visits a shop, picks up a pack, and decides — by eye, with a ruler — whether nine mandatory declarations are present, correctly worded, and printed at the legally required *height in millimetres*. India has millions of retail outlets and lakhs of SKUs. Coverage is single-digit percentage. Judgement is subjective and non-reproducible, so contested cases collapse in court.

**1.2 The e-commerce problem.** Rule 6 obligations extend to online listings, and the **Legal Metrology (Packaged Commodities) Amendment Rules, 2026** tightened them further — country of origin, net quantity and retail sale price must be displayed prominently on the listing page *before* purchase, with SKU-level origin tracking, and a transition window running to 1 July 2027. No inspector can manually audit a marketplace with 10⁸ listings. There is currently no scalable audit instrument.

**1.3 The industry's problem.** Manufacturers, packers and importers discover non-compliance *after* printing lakhs of pouches. Rework cost and seizure risk are large. The rules have changed materially in 2021, 2022, 2023, 2025 and 2026 — a brand team cannot reliably know which version applied on the date of packing.

**1.4 The consumer's problem.** A consumer has no way to know that a missing "consumer care" declaration or an under-height MRP is an offence, or how to report it with usable evidence.

> **Framing that wins:** this is not a scanning problem, it is a **measurement + adjudication** problem. The word "Metrology" is in the name of the law. A system that reads text but cannot state a font height in millimetres with a defensible error bound has not solved the problem statement.

---

## 2. The legal surface — what must actually be checked

All references are to the Legal Metrology (Packaged Commodities) Rules, 2011 ("LMPC") as amended, and the Legal Metrology Act, 2009 ("the Act").

### 2.1 Presence checks — Rule 6(1), declarations on every retail package

| # | Declaration | Citation |
|---|---|---|
| 1 | Name and address of manufacturer / packer; for imports, the importer | R.6(1)(a) |
| 2 | Country of origin / manufacture / assembly (imported products) | R.6(1)(aa) |
| 3 | Common or generic name of the commodity (each, if multi-product) | R.6(1)(b) |
| 4 | Net quantity in standard units of weight/measure/number | R.6(1)(c) |
| 5 | Month and year of manufacture / pre-packing / import | R.6(1)(d) |
| 6 | Best-before / use-by date, month, year (perishables) | R.6(1)(d) proviso |
| 7 | Retail sale price as **"Maximum Retail Price ₹ … inclusive of all taxes"** | R.6(1)(e) |
| 8 | Dimensions, where relevant | R.6(1)(f) |
| 9 | Consumer care details — name, address, phone/email for complaints | R.6(1) consumer-care provision |
| 10 | Unit sale price, where applicable | R.6 (2021/2022 amendments) |

### 2.2 Content and format checks

| Check | Rule | Machine-checkable predicate |
|---|---|---|
| MRP prefixed correctly, rounded to nearest rupee / 50 paise | R.6(1)(e) | regex + numeric modulo |
| Units: g/ml below 1 kg/l, kg/l at or above | R.13 | parse quantity → unit-class assertion |
| No "dozen", "gross", "score" notation | R.13 | lexical blocklist |
| No qualifiers — "approx.", "about", "minimum", "not less than" | R.11 | lexical blocklist |
| Net quantity excludes wrapper/packaging | R.11 | semantic flag |
| Language: Hindi (Devanagari) **or** English (others additionally permitted) | R.9(4) | script detection |
| Address completeness incl. PIN | R.10 | address parser |
| Declaration not readable only through the liquid contents | R.9(2) | heuristic + reviewer flag |
| Stickers must not alter mandatory declarations (MRP-reduction sticker permitted if original MRP visible) | R.6(3)–(4) | sticker/overlay detection |
| Unit sale price arithmetic = MRP ÷ net quantity | R.6 amendments | **computed** check — free-form false-claim detector |

### 2.3 Geometric / typographic checks — the differentiator

**Rule 7 — Principal Display Panel: area, size and letter.** Minimum height of numerals and letters is a function of PDP area:

| PDP area A (cm²) | Min height, normal (mm) | Min height, blown / moulded / embossed (mm) |
|---|---|---|
| A ≤ 50 | 1.0 | 1.5 |
| 50 < A ≤ 100 | 1.5 | 3.0 |
| 100 < A ≤ 500 | 2.5 | 4.0 |
| 500 < A ≤ 2500 | 4.0 | 6.0 |
| A > 2500 | 6.0 | 6.0 |

Also: width of a letter/numeral ≥ ⅓ of its height (except "1", i, I, l) — R.7(3).

PDP area is itself computed geometrically — R.7(4):
- **Rectangular pack:** height × width of that face
- **Cylindrical pack:** 40% × (height × circumference)
- **Other shapes:** 40% × total surface area
- Excluding tops, bottoms, can flanges, bottle/jar shoulders and necks

**Rule 8 — declaration placement.** Declarations must appear on the PDP, grouped together, with prescribed surrounding blank space.

**Rule 9(1)(b) — contrast.** MRP and net-quantity numerals must be in a colour that "contrasts conspicuously with the background". This is measurable — sample glyph pixels vs local background, compute a contrast ratio / ΔE.

### 2.4 Scope, exemption and precedence logic

A correct engine must decide *whether a rule applies at all* before applying it:

- **Retail vs wholesale package** — R.2(k) / R.2(r); wholesale packages take the reduced set at R.24.
- **Export packages** — R.25.
- **Exemptions — R.26:** net weight ≤ 10 g or volume ≤ 10 ml (10–20 g/ml still needs MRP and quantity); fast food from restaurants/hotels; scheduled formulations under the DPCO; agricultural produce in packages > 50 kg.
- **Statutory precedence:** the **2025 Amendment (notified 29 Oct 2025)** makes the Medical Devices Rules, 2017 prevail over LMPC for letter height/width and PDP placement on medical device packs, and bars R.33 relaxations for them. FSSAI labelling and the Drugs Rules similarly overlay food and pharma.
- **Temporal applicability:** the rule set in force on the *date of packing* governs. Given amendments in 2021, 2022, 2023, 2025 and 2026, a package packed in March 2022 must not be judged by 2026 rules.

### 2.5 Consequence mapping

| Instrument | Exposure |
|---|---|
| **Act s.36(1)** — non-standard packages | up to ₹25,000 (1st offence); ₹50,000 (2nd); ₹50,000–₹1,00,000 and/or imprisonment up to 1 year (subsequent) |
| **Act s.36(2)** — net quantity error | ₹10,000–₹50,000 (1st); up to ₹1,00,000 and/or up to 1 year (subsequent) |
| **LMPC R.32** | fine up to ₹4,000 (R.27–31 contraventions); up to ₹2,000 (other rules) |
| **LMPC R.32A** | compounding sums |

The escalating first/second/subsequent ladder in s.36 is *only usable if you can prove repeat offence* — which requires a national, queryable offence history. That is a direct product requirement, and a strong hook into **eMaap**, the Department of Consumer Affairs' National Legal Metrology Portal (licensing, verification, packer registration, enforcement and compounding, states onboarding since 2025).

---

## 3. Users and jobs to be done

| User | Job | What they need from the system |
|---|---|---|
| **Legal Metrology Inspector** (field) | Inspect a shop, decide seize/notice/compound | Offline scan → verdict in seconds → signed, evidence-backed report attachable to a case file |
| **State Controller of Legal Metrology** | Allocate scarce inspectors | Risk-ranked targets: brand, category, district, repeat offenders |
| **Department of Consumer Affairs (Centre)** | National compliance picture; e-commerce oversight | Cross-state analytics; marketplace audit at scale; amendment impact tracking |
| **Manufacturer / packer / importer** | Don't print non-compliant artwork | Pre-print artwork gate; batch SKU check; "which rule version applies" answer |
| **E-commerce marketplace** | Meet 2026 amendment obligations | Bulk listing compliance API at catalogue scale, SKU-level origin validation |
| **Consumer** | Report a bad pack; check before buying | Scan → plain-language verdict → one-tap complaint with evidence |

---

## 4. Proposed solution

### 4.1 Product concept

**A rules-as-code compliance engine for Legal Metrology, fed by three input lanes, producing evidence-grade verdicts.**

Working name suggestion: **MAAP-Check** / **Naap-Tol** / **PackCheck** — pick one that echoes eMaap so the ministry sees the fit.

**Lane A — Artwork (prevention, exact).** Manufacturer uploads the print-ready PDF/SVG/AI artwork with a dieline. Vector text carries *exact* glyph metrics and the dieline carries *exact* physical dimensions, so PDP area and every letter height are computed **deterministically, to two decimals of a millimetre — zero estimation error**. This lane alone is a shippable product for industry and is cheap to build. Almost no competing team will think of it.

**Lane B — Photograph (detection, estimated).** Inspector or consumer photographs the pack with a scale reference. Computer vision recovers the mm-per-pixel scale, rectifies the panel, reads the declarations, and measures glyph heights with a stated confidence interval.

**Lane C — Listing (e-commerce, structured).** Seller feed / marketplace API / user-submitted listing capture is checked for R.6 declarations plus the 2026 country-of-origin and unit-price obligations, and **cross-checked against the physical label** — a listing showing a different MRP or net quantity from the pack is a violation the current system cannot detect at all.

### 4.2 The scale problem, and how to solve it honestly

Measuring absolute millimetres from a photograph requires recovering metric scale. Design it as a **cascade with declared confidence**, never a guess:

| Tier | Method | Typical accuracy | Verdict grade |
|---|---|---|---|
| 1 | Printed **ArUco/April fiducial** card in frame (issued to inspectors) | ±1–2% | **Measurement-grade** |
| 2 | Known reference object — ₹5 coin (23 mm), credit/Aadhaar card (85.60 × 53.98 mm) | ±2–4% | Measurement-grade |
| 3 | **Device AR depth** (ARCore Raw Depth / ARKit / LiDAR) + intrinsics | ±3–6% | Indicative-strong |
| 4 | **EAN-13 barcode** width prior (nominal 37.29 mm at 100%, but magnification 80–200%) | ±20% | Indicative-weak |
| 5 | User-entered pack dimensions | depends on user | Indicative |
| — | No scale recoverable | — | **INDETERMINATE** |

**`INDETERMINATE` must be a first-class verdict alongside PASS / FAIL / NOT_APPLICABLE.** A system that guesses violations is worse than useless to a regulator, because one bad prosecution destroys trust in the tool. Only measurement-grade evidence is offered for enforcement action; everything else is a *lead* for a physical inspection. Saying this explicitly in the pitch signals institutional maturity that hackathon judges from a ministry respond to.

For the Rule 7 threshold specifically, add a **borderline band**: if the measured height ± CI straddles the threshold (e.g. measured 2.4 ± 0.15 mm against a 2.5 mm requirement), return `BORDERLINE — physical verification required`, not `FAIL`.

### 4.3 The rule engine

The core asset is not the ML — it is the **machine-readable rule pack**.

```yaml
- id: LMPC.R7.2.letter_height
  citation: "Rule 7(2) r/w Table-I, LMPC Rules 2011"
  title: "Minimum height of letters and numerals"
  effective_from: 2011-04-01
  effective_to: null
  applies_when:
    package_type: retail
    not_exempt_under: [R26.a, R26.b, R26.d]
    precedence_yields_to: [MedicalDevicesRules2017]   # 2025 Amendment
  inputs: [pdp_area_cm2, surface_type, measured_glyph_height_mm]
  predicate: "measured_glyph_height_mm >= threshold(pdp_area_cm2, surface_type)"
  severity: major
  exposure: "Act s.36(1); LMPC R.32"
  remedy: "Increase declaration type size to at least {threshold} mm."
  evidence_required: [scale_method, glyph_bbox, pdp_geometry]
```

Properties that matter:

1. **Declarative and versioned in git** — a Legal Metrology officer can review a diff, not Python.
2. **Temporally versioned** — `effective_from` / `effective_to` on every rule; the engine selects the rule set as at the pack's date of manufacture. This handles the 2021→2026 amendment churn and is a genuinely novel angle.
3. **Precedence-aware** — medical devices, food, drugs.
4. **Exemption-first evaluation** — applicability is decided before compliance.
5. **Every verdict carries its citation, evidence crop, measured value, required value, remedy and penalty exposure.** Never a bare "non-compliant".
6. **A golden test suite** — synthetic and real labels with known verdicts, run in CI. Rule changes cannot silently regress.

### 4.4 Reference architecture

```
                    ┌──────────────── INGEST ────────────────┐
  Inspector app ───►│ capture + on-device pre-check (offline) │
  Consumer app  ───►│                                          │
  Artwork portal───►│ PDF/SVG vector parse (exact metrics)     │
  Marketplace API ─►│ listing feed adapter                     │
                    └──────────────┬───────────────────────────┘
                                   ▼
                    ┌──────── PERCEPTION ─────────┐
                    │ pack detect + segment (YOLO/SAM)
                    │ pack-type classify (box/bottle/pouch/can/jar)
                    │ scale recovery cascade (ArUco→ref obj→AR depth→barcode)
                    │ panel rectify (homography; cylindrical unwrap)
                    │ OCR: PaddleOCR en + Devanagari, char-level bboxes
                    │ barcode/QR decode → GTIN
                    │ photometry: glyph vs background contrast
                    └──────────────┬──────────────┘
                                   ▼
                    ┌──── EXTRACTION & NORMALISATION ────┐
                    │ VLM structured extraction → LabelFacts JSON
                    │ (schema-constrained; OCR text + crops as evidence)
                    │ unit/date/price/address parsers
                    │ GTIN → product master + packer registry lookup
                    └──────────────┬──────────────┘
                                   ▼
                    ┌────────── RULE ENGINE ──────────┐
                    │ applicability → exemptions → precedence
                    │ temporal rule-set selection by pack date
                    │ presence | content | geometric | cross-source checks
                    │ verdicts: PASS/FAIL/NA/BORDERLINE/INDETERMINATE
                    └──────────────┬──────────────┘
                                   ▼
        ┌──────────── EVIDENCE & WORKFLOW ────────────┐
        │ signed evidence bundle (image hash, EXIF, geo, model+ruleset version)
        │ human-in-the-loop review & override → active-learning queue
        │ case file / notice / compounding draft (eMaap-ready)
        │ repeat-offender ledger → s.36 first/second/subsequent ladder
        └──────────────┬──────────────────────────────┘
                       ▼
        Dashboards: state/district heatmap • brand & category risk •
        amendment-impact tracker • marketplace scorecards • targeting queue
```

### 4.5 Technology choices

**Hackathon build (48-hour-demoable):**

| Layer | Choice | Why |
|---|---|---|
| Mobile | Flutter (or React Native) + ONNX Runtime / TFLite | one codebase, on-device inference, offline-first |
| Scale | OpenCV ArUco + ARCore Raw Depth | deterministic tier-1, impressive tier-3 |
| Detection/segmentation | YOLOv8n-seg / SAM2 (distilled) | fast, runs on-device |
| OCR | PaddleOCR (en + devanagari), char-level boxes | best open Indic OCR; char boxes needed for mm measurement |
| Barcode | ZXing / pyzbar | GTIN linkage |
| Field extraction | Qwen2.5-VL 7B (or similar) with JSON-schema-constrained output | robust to OCR noise; grounded in crops |
| Artwork lane | pdfplumber / PyMuPDF + fontTools | exact glyph metrics from vector PDF |
| Backend | FastAPI + Celery/Redis, Postgres (+pgvector), MinIO | fast to stand up, async pipeline |
| Rule engine | Python + Pydantic-validated YAML rule packs | reviewable by non-engineers |
| Frontend | Next.js + React, Mapbox/Leaflet for heatmaps | |
| Deploy | Docker Compose (demo) | one command for judges |

**Production / scale-out narrative (say this, don't build it):** Kafka ingestion bus for marketplace catalogue sweeps; Temporal for durable, retryable multi-stage inspection workflows with human-in-the-loop signals; LangGraph for the extraction→verification→adjudication agent graph with explicit checkpoints; Kubernetes with GPU node pools for the perception tier; deployment on NIC/MeghRaj or a state cloud; API contracts aligned to eMaap.

### 4.6 Data strategy — this is where you get real numbers

No public LMPC-annotated dataset exists. Build one; it becomes a defensible asset.

1. **Real benchmark set (300–500 packs).** Photograph across categories (food, beverages, cosmetics, detergents, staples, imported goods) and pack geometries. Ground-truth every declaration, and **measure actual glyph heights with a vernier caliper**. This gives you a font-height MAE in mm — a number no other team will have.
2. **Synthetic label generator.** Programmatically render labels with *known* mm glyph heights, PDP areas, contrast ratios, languages, and deliberately injected violations; then apply domain randomisation — perspective, curvature, glare, metallised foil, blur, crumple, shadow. Unlimited perfectly-labelled data for both training and quantitative evaluation. Cheap, and it directly de-risks the hardest measurement.
3. **Listing corpus.** Use seller-provided feeds, official marketplace APIs, or user-submitted screenshots. **Do not scrape marketplaces** — it is a terms-of-service and legal risk you do not need in a government-facing demo.
4. **Adversarial set.** Compliant-looking-but-not packs: sticker over MRP, unit price arithmetic wrong, correct fields at sub-threshold height, origin missing on an imported good.

### 4.7 Metrics to put on a slide

- Per-field extraction precision / recall / F1 (10 declaration fields)
- **Font-height MAE (mm)** vs caliper ground truth, by scale tier
- Rule 7 pass/fail classification accuracy, and **false-positive rate on compliant packs** — target < 1%, this is the number a regulator cares about
- % of scans reaching measurement-grade vs indicative vs indeterminate
- End-to-end latency: on-device pre-check, full server verdict
- Throughput: listings audited per hour
- Rule-pack coverage: N rules encoded / M checkable rules

---

## 5. Scope — build vs. pitch

**Must build (a working end-to-end MVP beats a broad broken one):**

1. Inspector capture flow with ArUco/card scale → rectify → OCR (en + hi) → field extraction
2. Rule engine with **~20 highest-value rules**, including Rule 7 font height with genuine mm measurement and confidence
3. Verdict screen: per-rule PASS/FAIL/BORDERLINE/INDETERMINATE with citation, annotated evidence crop, measured vs required, remedy
4. Signed PDF inspection report with evidence hashes and version stamps
5. Controller dashboard over a few hundred pre-scanned SKUs: heatmap, brand risk, repeat-offender ledger
6. **Artwork lane** — upload a PDF, get exact deterministic compliance (high impact, low effort)
7. E-commerce listing check demo on 2–3 saved listing pages, including label↔listing cross-check

**Pitch, don't build:** consumer app + NCH/e-Daakhil complaint routing, live eMaap integration, active learning loop, AR live-overlay measurement, national rollout economics.

---

## 6. Why this wins — the eight differentiators

1. **Metrology, not OCR.** Real millimetre measurement with a stated error bound, because the law is a measurement law.
2. **Rules-as-code with temporal versioning.** Judges the pack by the rules in force on its date of packing — 2021, 2022, 2023, 2025, 2026.
3. **Evidence-grade output.** Signed, hashed, versioned bundle usable in a compounding or prosecution file.
4. **Prevention + detection.** Artwork gate for industry *and* field/e-commerce detection for the regulator — the whole lifecycle.
5. **INDETERMINATE as a feature.** Never manufactures a violation; separates enforceable findings from inspection leads.
6. **Offline-first.** Works in rural markets with no connectivity — matching the theme.
7. **eMaap-shaped.** Repeat-offender ledger mapped to the s.36 escalation ladder; packer-registration lookup; compounding workflow hooks.
8. **Its own benchmark + synthetic generator.** Quantitative accuracy claims, not demo-day anecdotes.

---

## 7. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Font-height accuracy insufficient for enforcement | Core claim fails | Mandatory fiducial in v1; publish MAE by tier; BORDERLINE band; INDETERMINATE fallback |
| OCR fails on curved, reflective, metallised, crumpled packs | Extraction gaps | Cylindrical unwrap; multi-shot fusion; polarised/flash guidance in capture UI; VLM fallback on crops |
| Devanagari + regional-script OCR quality | Misses Hindi-only labels | Fine-tune PaddleOCR on synthetic Devanagari labels; VLM cross-read |
| Rule encoding legally wrong | Credibility loss | Inline rule text with every verdict; rule pack reviewed against bare Act/Rules; golden test suite; explicit "advisory, not adjudicatory" disclaimer |
| PDP area estimation error propagates into the wrong threshold band | Wrong verdict | Require pack-type selection + two-view capture; allow manual dimension entry; propagate uncertainty into the band decision |
| Marketplace scraping | Legal/ToS exposure | Feeds, official APIs, user-submitted captures only |
| Over-automation of enforcement | Ministry rejection | Human-in-the-loop mandatory; system proposes, officer disposes |
| Scope sprawl across four lanes in a short build | Nothing works end-to-end | Freeze to the seven must-build items; lanes share one rule engine |

---

## 8. Suggested next steps

1. **Verify the PS on sih.gov.in** — confirm SIH26034's official description, expected-solution text, deadline and any dataset links before locking scope.
2. **Encode the first rule pack** (20 rules) with citations and a golden test suite — do this before writing any ML code; it is the artefact that defines the product.
3. **Build the synthetic label generator** — it unblocks both training and evaluation.
4. **Prototype the scale cascade** on 30 real packs with caliper ground truth; report MAE. If tier-1 does not reach ±2%, redesign the capture UX before building anything else.
5. **Draft the idea-submission deck** around the eight differentiators in §6, leading with the metrology framing.

---

## Sources

- [Legal Metrology (Packaged Commodities) Rules, 2011 — full text](https://legalmetrologymh.in/public/temp/368/02d3c4fef3045bc21d90ba000a28357e.pdf)
- [Rule 6 — Declarations to be made on every package (Indian Kanoon)](https://indiankanoon.org/doc/38209662/)
- [Legal Metrology (Packaged Commodities) Rules, 2011 (mirror)](https://foodsafetystandard.in/wp-content/uploads/2019/11/LM-Packaged-Commodities-Rules-2011.pdf)
- [Section 36, Legal Metrology Act, 2009 — penalties](https://lawgist.in/legal-metrology-act/36)
- [Legal Metrology (Packaged Commodities) Amendment Rules, 2022 — analysis](https://www.saikrishnaassociates.com/ministry-of-consumer-affairs-notifies-the-legal-metrology-packaged-commodities-amendment-rules-2022/)
- [PIB — Legal Metrology (Packaged Commodities) Amendment Rules, 2025 (medical devices harmonisation)](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2183777&reg=48&lang=2)
- [Legal Metrology (Packaged Commodities) Amendment Rules, 2026 — e-commerce disclosure](https://www.mondaq.com/india/dodd-frank-consumer-protection-act/1806934/legal-metrology-packaged-commodities-amendment-rules-2026-enhancing-transparency-and-consumer-protection-in-e-commerce)
- [PIB — eMaap, National Legal Metrology Portal](https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2080446)
- [SIH 2026 problem statement catalogue (SIH26034)](https://github.com/NoBugNinja/Smart-India-Hackathon-SIH-2026-Problem-Statements)
- [SIH 2026 master catalogue PDF](https://blinknbuild.in/Assets/SIH_2026_All_226_Problem_Statements_Master_Catalogue.pdf)
