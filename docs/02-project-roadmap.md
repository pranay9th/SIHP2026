# SIH26034 — What Needs to Be Done

**A step-by-step plan for a first-year B.Tech team**

Problem Statement: *Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels.*
PS ID: **SIH26034** · Ministry of Consumer Affairs, Food & Public Distribution · Software track

> **Read this first.** There is a companion document, `01-problem-analysis.md`, which is the deep technical analysis. It is deliberately ambitious — it describes the *full* system. **You are not expected to build all of it.** This document tells you what to actually do, in order, at a level a first-year team can deliver.

---

## ⚠️ Verify these three things before anything else

Different websites give different information. Only **sih.gov.in** counts.

| Thing to check | What sources say | Action |
|---|---|---|
| Idea submission deadline | One source says **15 Sep 2026**, another says **20 Sep 2026** | Check the portal *today*. Assume the earlier date and plan accordingly. |
| Official PPT template | Format varies year to year | Download the official template from sih.gov.in and use **that file**, not a copy from a blog |
| Full PS description | Ministries often add an "expected solution" paragraph | Read the full text on the portal; it may narrow the scope |

**Do this first, today.** Everything below assumes the earlier deadline.

---

## 1. Understanding the problem in one page

### The law, in plain English

When you buy a packet of biscuits, a bottle of shampoo or a bag of rice, the law says the packet **must** print certain things on it. This law is the *Legal Metrology (Packaged Commodities) Rules, 2011*. "Metrology" just means **the science of measurement**.

Here are the things every retail packet must show:

| # | What must be printed | Example |
|---|---|---|
| 1 | Who made or packed it, and their address | *Manufactured by: ABC Foods Pvt Ltd, Plot 12, Pune – 411001* |
| 2 | Country of origin (only if imported) | *Country of Origin: Vietnam* |
| 3 | What the product is (common name) | *Salted Biscuits* |
| 4 | Net quantity | *Net Wt. 200 g* |
| 5 | Month and year it was made or packed | *Mfd: 03/2026* |
| 6 | Best before / use by (for food and perishables) | *Best Before 9 months from packing* |
| 7 | Maximum Retail Price, with the exact wording | *MRP ₹40 (inclusive of all taxes)* |
| 8 | Dimensions, where relevant | *30 cm × 20 cm* |
| 9 | Consumer care details — name, address, phone or email | *Customer Care: 1800-xxx-xxxx, care@abc.in* |

Plus, for some products, the **unit sale price** (price per gram, per ml or per piece).

### The part almost everyone misses

The law does not only say *"print the MRP."* It says **how big the letters must be**, measured in millimetres. And the required size depends on how large the front of the packet is:

| Size of the front panel (PDP) | Minimum letter height |
|---|---|
| Up to 50 cm² | 1.0 mm |
| 50 – 100 cm² | 1.5 mm |
| 100 – 500 cm² | 2.5 mm |
| 500 – 2500 cm² | 4.0 mm |
| More than 2500 cm² | 6.0 mm |

*(PDP = Principal Display Panel = the main front face of the pack. On a bottle or tin, it's 40% of height × circumference.)*

So a company can print everything correctly and **still be breaking the law** because the text is 2.1 mm when it needed to be 2.5 mm. A shopper cannot see this. An inspector with a ruler struggles to see it. **A camera plus software can measure it exactly.**

> **This one insight is the heart of your project.** Write it on a sticky note.

### Who has this problem today

- **Legal Metrology Inspectors** — government officers who visit shops and check packets by hand, with a ruler. There are lakhs of shops and only a few thousand inspectors. They can check a tiny fraction.
- **Online shopping sites** — new rules notified in 2026 require product listing pages to show country of origin, net quantity and price. No human can check crores of listings.
- **Companies** — they find out their packet design was illegal only *after* printing lakhs of wrappers.
- **Consumers** — no easy way to check or complain.

### The penalties (useful for your Impact slide)

Under Section 36 of the Legal Metrology Act, 2009: **up to ₹25,000** for a first offence, **₹50,000** for a second, and **₹50,000 to ₹1,00,000 plus up to one year's imprisonment** for repeat offences.

---

## 2. Your solution, in one sentence

> **A phone or web app where you photograph a packet next to a small printed reference card. The software reads all the mandatory declarations, actually measures the letter heights in millimetres, checks everything against the 2011 Rules, and produces a report card showing exactly which rule passed, which failed, and why.**

Say this sentence out loud until it sounds natural. It is your entire pitch.

### The three things that make it special

**1. It measures, it doesn't just read.**
Most teams attempting this problem will build an app that reads text off a label. Yours *measures* — because the law is a measurement law. The reference card in the photo is what makes this possible: the card is a known physical size, so the software can work out how many millimetres each pixel represents, and from there, how tall each letter is.

**2. It says "I don't know" when it doesn't know.**
If the photo is blurry, or the reference card is missing, or the measurement is right on the borderline (say 2.4 mm against a 2.5 mm requirement), the app must **not** say "VIOLATION". It says **NEEDS PHYSICAL CHECK**. A government tool that falsely accuses a shopkeeper is worse than no tool at all. Judges from a ministry will notice that you thought about this. Almost no student team will.

**3. Every result cites the exact rule.**
Not "non-compliant" but *"FAIL — Rule 7(2), Table-I: letter height measured 2.1 mm, minimum required 2.5 mm for a 240 cm² front panel."* An officer can attach that to a real case file.

### What you show on screen

```
   📷  Photo of pack + reference card
                 ↓
   ┌─────────────────────────────────┐
   │  COMPLIANCE REPORT CARD          │
   ├─────────────────────────────────┤
   │ ✅ Manufacturer name & address   │
   │ ✅ Common name of commodity      │
   │ ✅ Net quantity — "200 g"        │
   │ ❌ MRP wording — missing         │
   │    "inclusive of all taxes"      │
   │    → Rule 6(1)(e)                │
   │ ❌ Letter height — 2.1 mm        │
   │    Required 2.5 mm (Rule 7)      │
   │ ⚠️  Consumer care — unclear,     │
   │    needs physical check          │
   ├─────────────────────────────────┤
   │  SCORE: 6 / 9 declarations       │
   │  [ Download PDF report ]         │
   └─────────────────────────────────┘
```

---

## 3. What to actually build

Split everything into three buckets. **Be ruthless about this.** The most common way student teams fail is building a little bit of everything and finishing nothing.

### 🟢 MUST BUILD — the core demo

Without these you have nothing to show.

| # | Feature | What it means | Difficulty |
|---|---|---|---|
| 1 | Upload or capture a photo | A web page with a file-upload button and a camera option | Easy |
| 2 | Read the text off the label | Use a ready-made OCR library — do **not** write your own | Easy |
| 3 | Pull out the 9 declarations | Find MRP, net quantity, dates etc. in the messy OCR text using pattern matching | Medium |
| 4 | Check ~12 rules | Simple Python `if` conditions — is MRP present? is the wording right? are the units correct? | Easy |
| 5 | **Measure letter height in mm** | Detect the reference card, calculate mm-per-pixel, measure text box heights | **Medium — this is your star feature** |
| 6 | Show the report card | Green tick / red cross per rule, with the rule number and the reason | Easy |
| 7 | Download a PDF report | Generate a simple PDF of the results | Easy |

### 🟡 SHOULD BUILD — if time allows

| # | Feature | Why it's worth it |
|---|---|---|
| 8 | Dashboard with charts | Scan 30–50 real packets, show which brands and categories fail most. Makes the demo feel like a real system, not a toy. |
| 9 | Hindi text support | The law allows Hindi or English. Most OCR libraries support Devanagari with one setting change. Cheap credibility. |
| 10 | Compare label vs online listing | Paste a product page's details, check if the MRP and quantity match the physical pack. Directly addresses the 2026 amendment. |

### 🔴 DO NOT BUILD — pitch as "future scope"

These belong on your last slide, described in one line each. Building them will sink you.

- A native Android/iOS app *(a mobile-friendly website is enough)*
- Automatic scraping of Amazon or Flipkart *(also a legal risk — never mention scraping to a government panel)*
- Training your own AI model from scratch
- Blockchain *(judges are tired of it)*
- Integration with government systems
- 3D reconstruction of packet shape

---

## 4. Technology — the beginner-friendly stack

Everything here is free, Python-based, and learnable in days. **Resist the urge to pick fancier tools.**

| Layer | Use this | Why |
|---|---|---|
| Language | **Python** | One language for the whole project. No context switching. |
| Web interface | **Streamlit** | A working web app in ~40 lines of Python. No HTML, CSS or JavaScript needed. This single choice saves you a week. |
| Reading text | **EasyOCR** (or PaddleOCR) | One line to install, supports English + Hindi, gives you a box around every piece of text — and you need those boxes to measure heights. |
| Image handling & measuring | **OpenCV** (`opencv-python`) | Detects the reference card. `cv2.aruco.detectMarkers()` is about five lines of code. |
| Rules | **A JSON file + plain Python** | Keep the 2011 Rules in a JSON file, not scattered through your code. Looks professional and is easier to edit. |
| Storing scans | **SQLite** | A database in a single file. No server to install. |
| Charts | **Plotly** (built into Streamlit) | Three lines per chart. |
| PDF report | **fpdf2** or **reportlab** | Simple text-and-image PDFs. |
| Code sharing | **GitHub** | Judges may ask. Also stops you emailing `final_final_v3.py` to each other. |

**Install everything with one command:**

```bash
pip install streamlit easyocr opencv-python opencv-contrib-python pandas plotly fpdf2
```

### How the letter-height measurement actually works

This sounds like the hard part. It isn't. Here is the whole idea:

1. Print an **ArUco marker** (a small black-and-white square pattern — generate one free online) at exactly **50 mm × 50 mm**. Stick it on a piece of card.
2. Place that card next to the packet and take one photo of both.
3. OpenCV finds the marker and tells you its four corners in pixels. Say it measures **200 pixels** wide.
4. So **200 pixels = 50 mm**, therefore **1 pixel = 0.25 mm**. That is your scale.
5. OCR gives you a box around the text "MRP ₹40". Say that box is **9 pixels** tall.
6. Letter height = 9 × 0.25 = **2.25 mm**.
7. Compare against the table in Rule 7. Done.

That's roughly 30 lines of code and it is the most impressive thing in your entire project. **Build this early**, because if it doesn't work you need to know in week one, not week four.

> ⚠️ Two honest cautions. Keep the camera **straight on** and **parallel** to the pack — tilt introduces error. And measure the text box height, then note that OCR boxes usually include a little padding, so calibrate against a few labels you've measured by hand with a ruler or vernier caliper. Reporting "±0.2 mm accuracy, verified against 20 hand-measured labels" is far stronger than claiming perfection.

---

## 5. Who does what — six roles

SIH teams are **6 members, at least one female member, all from the same college**. Give everyone one clear thing to own.

| Role | Owns | Good for someone who… |
|---|---|---|
| **1. Team Lead & Presenter** | The story, the deck, the demo script, deadlines, portal submission | speaks confidently and chases people |
| **2. Vision & OCR** | Camera input, image cleanup, running OCR, getting clean text out | enjoys tinkering until something works |
| **3. Measurement** | ArUco detection, mm-per-pixel, letter height, accuracy testing | likes maths and precision |
| **4. Rule Engine** | The JSON rule file, the compliance checks, the report card logic | is organised and detail-oriented |
| **5. Interface & Dashboard** | The Streamlit app, layout, charts, PDF export | cares how things look |
| **6. Research & Data** | Reading the Rules, buying/photographing 40 sample packets, hand-measuring ground truth, references slide | is thorough and patient |

**A note for role 6:** this is not the "leftover" job. Your team's biggest advantage over other teams will be **real data from real packets**. Nobody else will have hand-measured 40 labels. This role produces the numbers that make your presentation believable.

### If your team is smaller or less experienced

Merge roles 2 and 3 (both are OpenCV work), and merge 4 and 5. Four people can do this. Do not add a seventh person to "help" — it slows everything down.

---

## 6. The plan, week by week

### Stage 0 — Right now (Days 1–2)

- [ ] Open **sih.gov.in**, read the full official PS text for SIH26034, note the real deadline
- [ ] Confirm your college is running an internal hackathon and who the SPOC is *(only teams selected through the internal hackathon can register for SIH)*
- [ ] Form the team of 6, assign the roles above
- [ ] Download the **official PPT template** from the portal
- [ ] Create a WhatsApp group and a shared Google Drive folder

### Stage 1 — Understand and collect (Days 3–5)

- [ ] Everyone reads Section 1 of this document. Everyone.
- [ ] Go to a supermarket. Photograph **40 packets** — biscuits, shampoo, rice, soap, imported chocolate, a cold drink bottle, a tin. Get a mix of shapes.
- [ ] For **10 of them**, measure the MRP letter height by hand with a ruler or borrowed vernier caliper. Write it down. *This is your ground truth.*
- [ ] Note which packets are already breaking rules — you will find some. Those become your demo examples.
- [ ] Print the ArUco reference card

### Stage 2 — A tiny working proof (Days 6–9)

**Goal: one photo in, one report card out.** Ugly is fine.

- [ ] Streamlit page with an upload button
- [ ] EasyOCR running, printing whatever text it finds
- [ ] ArUco detection working, printing mm-per-pixel
- [ ] Three rules checked: MRP present, net quantity present, letter height vs Rule 7
- [ ] **Screenshot it.** This screenshot goes in your presentation and it is worth more than any diagram.

> Most teams submit a deck with only mockups. A deck with a screenshot of something that actually ran puts you in a different category.

### Stage 3 — The presentation (Days 10–14)

- [ ] Fill in the official template using `03-presentation-guide.md`
- [ ] Draw your own diagrams — do not paste images from Google
- [ ] Rehearse out loud, 5 times, timed
- [ ] Show it to a senior or a professor and ask them to attack it
- [ ] Fix what they broke

### Stage 4 — Submit (Day 15, not the deadline day)

- [ ] Export to **PDF** (submission is in PDF)
- [ ] Check the PS ID reads exactly `SIH26034`
- [ ] Upload. Screenshot the confirmation.

> **Submit two days early.** The portal always crawls on the last day.

### Stage 5 — If you're selected (later)

Build out the 🟡 SHOULD list, polish the dashboard, add Hindi, prepare a 5-minute live demo with a backup video in case the wifi dies. The Grand Finale is in December 2026 — you'll have months.

---

## 7. What the judges score you on

The official criteria are: **novelty, complexity, clarity and detail in the prescribed format, feasibility, practicability, sustainability, scale of impact, user experience, and potential for future work.**

Here's how your project answers each one:

| Criterion | Your answer |
|---|---|
| **Novelty** | Everyone else will read labels. You *measure* them in millimetres. |
| **Complexity** | Scale recovery from a reference marker, geometric PDP calculation, a rule engine with exemptions |
| **Clarity** | Use the official template, fill every box, no empty space |
| **Feasibility** | All open-source Python, and you have a working screenshot |
| **Practicability** | Solves a real job an inspector does today with a ruler |
| **Sustainability** | Rules stored in a JSON file, so the system survives amendments — 2021, 2022, 2023, 2025, 2026 |
| **Scale of impact** | Millions of shops, crores of online listings, every consumer in India |
| **User experience** | One photo → one clear report card |
| **Future work** | Online listing checks, artwork pre-check for manufacturers, national dashboard |

---

## 8. Mistakes to avoid

1. **Building an app that only reads text.** That's a photo-to-text converter, not a compliance system. Measurement is the point.
2. **Claiming 99% accuracy.** Judges will ask how you measured it. If you can't answer, you lose the room. Say "±0.2 mm on 20 hand-measured labels" instead — a small honest number beats a big invented one.
3. **Saying you'll scrape Amazon.** Never say this to a government panel. Say "seller feeds, official APIs, or user-submitted screenshots."
4. **Copying the problem statement onto your slide.** Judges wrote it. Restate it in your own words.
5. **A deck full of text.** Judges see hundreds. Use diagrams, screenshots, and short lines.
6. **Everyone coding, nobody presenting.** The idea round is judged **only on the deck.** Someone must own it full time.
7. **Starting the PPT on the last day.**
8. **Using stock images of robots and AI brains.** Use screenshots of your own work.

---

## 9. Free things to learn, in order

Only learn what you need, in the order you need it.

| Week | Learn | Where | Time |
|---|---|---|---|
| 1 | Python basics: lists, dicts, functions, `if` | You may already know this | — |
| 1 | Streamlit — one tutorial is enough | docs.streamlit.io "Get started" | 2 hrs |
| 2 | Reading images with OpenCV | OpenCV Python tutorials | 3 hrs |
| 2 | EasyOCR — literally 3 lines | Its GitHub README | 1 hr |
| 2 | ArUco markers | OpenCV ArUco tutorial | 2 hrs |
| 3 | Regex (pattern matching) for pulling out MRP, dates | regex101.com — practise there | 3 hrs |
| 3 | Git & GitHub basics | GitHub "Hello World" guide | 2 hrs |

**Total: about 13 hours.** Split across six people, that's nothing.

---

## 10. Questions judges will ask — and your answers

**"How do you measure millimetres from a photo?"**
> A reference marker of known physical size in the same frame gives us the millimetres-per-pixel scale. We measured our error against 20 hand-measured labels: ±0.2 mm.

**"What if the photo is blurry or tilted?"**
> The app refuses to give a verdict. It returns NEEDS PHYSICAL CHECK. We never guess a violation, because a false accusation against a shopkeeper is a worse outcome than no answer.

**"OCR isn't perfect. What about wrong readings?"**
> Correct — which is why the officer reviews and confirms before any action. The system flags and evidences; the human decides. It also shows the cropped image next to every reading so an officer can verify in one glance.

**"The rules keep changing. Will this become outdated?"**
> The rules live in a separate JSON file with valid-from and valid-to dates, not inside the code. When a rule changes, someone edits the file — no reprogramming. We can also judge a packet by the rules in force on its date of packing, which matters because the rules changed in 2021, 2022, 2023, 2025 and 2026.

**"What's actually working today?"**
> Show the screenshot. Say plainly what works and what doesn't. Honesty scores; bluffing gets caught.

**"Isn't this just OCR?"**
> OCR is one component. OCR tells you the MRP is printed. It cannot tell you the MRP is printed 0.4 mm too small — and that under-height printing is itself the offence under Rule 7.

---

## 11. Quick reference — rules to encode first

Start with these twelve. They cover most real violations and are all simple to check.

| # | Rule | Check |
|---|---|---|
| 1 | R.6(1)(a) | Manufacturer/packer name and address present |
| 2 | R.6(1)(b) | Common or generic name present |
| 3 | R.6(1)(c) | Net quantity present |
| 4 | R.6(1)(d) | Month and year of manufacture present |
| 5 | R.6(1)(e) | MRP present |
| 6 | R.6(1)(e) | MRP says "inclusive of all taxes" |
| 7 | R.6(1)(e) | MRP rounded to nearest rupee or 50 paise |
| 8 | R.6(1) | Consumer care contact present |
| 9 | R.6(1)(aa) | Country of origin present, if imported |
| 10 | R.11 | No vague words — "approx.", "about", "minimum" |
| 11 | R.13 | Correct units — g/ml below 1 kg/l, kg/l at or above; no "dozen" |
| 12 | **R.7(2) Table-I** | **Letter height ≥ required minimum for the panel area** ⭐ |

Two more once those work: **R.9(4)** language must be English or Hindi; **R.26** exemptions — skip packs of 10 g/ml or less.

---

## Sources

- [Legal Metrology (Packaged Commodities) Rules, 2011 — full text](https://legalmetrologymh.in/public/temp/368/02d3c4fef3045bc21d90ba000a28357e.pdf)
- [Rule 6 — Declarations to be made on every package](https://indiankanoon.org/doc/38209662/)
- [Section 36, Legal Metrology Act 2009 — penalties](https://lawgist.in/legal-metrology-act/36)
- [SIH 2026 guidelines — team rules, stages, judging criteria](https://sih-uit.vercel.app/assets/sih-2026-guidelines.pdf)
- [SIH 2026 problem statement catalogue](https://github.com/NoBugNinja/Smart-India-Hackathon-SIH-2026-Problem-Statements)
- [PIB — Amendment Rules 2026, e-commerce disclosure](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2183777&reg=48&lang=2)
