# START HERE

**A reading guide for this repository.**
If you have just been given this link and don't know where to begin, you are in the right place. Read this page, then follow the order below.

---

## What this repository is

This is a Smart India Hackathon 2026 project for problem statement **SIH26034**, set by the Ministry of Consumer Affairs, Food & Public Distribution.

**The problem:** every packet you buy in a shop must legally print nine things — who made it, what it is, how much is inside, the price, and so on. The law also says **how tall those letters must be, in millimetres.** Nobody can check that by eye.

**What we built:** photograph a packet next to a small printed card, and the software reads the declarations, **measures the letter heights in millimetres**, and tells you exactly which rule passed, which failed, and why.

**The one sentence to remember:**

> The law says the MRP must be printed at least 2.5 mm tall. Nobody can check that by eye. We measure it from a photograph.

---

## Before anything else: three things to verify

Don't plan around these until you've checked **sih.gov.in** yourself.

| Thing | What we found | Why check |
|---|---|---|
| Idea submission deadline | Sources say 15 Sep and 20 Sep 2026 | Five days is a lot when you have three weeks |
| Official PPT template | Format changes each year | Judges expect the official one |
| Full problem statement text | Ministries often add an "expected solution" paragraph | It may narrow the scope |

---

## Read in this order

Roughly a week of evenings. **Don't skip ahead to the code** — it will not make sense without the first two days.

### Day 1 — Understand the problem (about 2 hours)

| # | Read | Time | Why |
|---|---|---|---|
| 1 | `topic/topic.txt` | 1 min | The original problem statement, one line |
| 2 | `README.md` | 10 min | What exists, what works, what doesn't |
| 3 | **`docs/02-project-roadmap.md`** — sections 1 and 2 | 45 min | **The most important read.** The law explained in plain English, the nine declarations, the letter-height table |
| 4 | `docs/02-project-roadmap.md` — the rest | 45 min | What to build, team roles, week-by-week plan, mistakes to avoid |

> **Stop after Day 1 and check yourself.** Can you explain, without looking, why a packet with every declaration printed correctly might still be illegal? If not, re-read section 1 of the roadmap. Everything else builds on it.

### Day 2 — See it working (about 2 hours)

| # | Read / do | Time | Why |
|---|---|---|---|
| 5 | `docs/05-running-the-demo.md` — sections 1 to 5 | 20 min | Setup steps |
| 6 | **Actually install and run it** | 60 min | Nothing replaces seeing it work |
| 7 | Try all five sample labels in the app | 20 min | Watch how the verdict changes and why |
| 8 | `docs/05-running-the-demo.md` — the demo script | 15 min | How to present it in five minutes |

While the app is open, do these four things:

1. Scan `compliant_biscuits` — everything green
2. Scan `undersize_letters` — one red FAIL on Rule 7. **This is the whole project in one screen.** The label is perfectly printed and perfectly legible; the text is just too small
3. Set "Net quantity" in the sidebar to **8** — watch every rule turn to NOT APPLICABLE, because Rule 26 exempts packets of 10 g or less
4. Tick "Medical device" — watch the letter-height rule step aside, because a 2025 amendment hands that to a different rulebook

### Day 3 — Understand the code (about 3 hours)

Read the files in **this order**. It follows the path a photograph actually takes through the system, so each file explains the next. Every file starts with a comment saying what it does and why.

| # | File | Lines | What it does |
|---|---|---|---|
| 9 | `src/naaptol/models.py` | 202 | The vocabulary: what a TextBox, a ScaleEstimate, a Finding is. Read first — everything else uses these |
| 10 | `src/naaptol/geometry.py` | 96 | The smallest and clearest file. Rule 7 maths: panel area in, required millimetres out |
| 11 | `config/rules/lmpc-2011.json` | — | **Not code.** The rules themselves, as data. Skim it and notice every rule carries its citation, severity and remedy |
| 12 | `src/naaptol/scale.py` | 226 | How millimetres come out of a photograph. The heart of the project |
| 13 | `src/naaptol/ocr.py` | 336 | Reading text, and finding the exact edge of each letter |
| 14 | `src/naaptol/quality.py` | 140 | Deciding whether a photo is good enough to judge at all |
| 15 | `src/naaptol/extract.py` | 268 | Pulling the nine declarations out of messy text |
| 16 | `src/naaptol/rules.py` | 403 | The rule engine. The biggest file — leave it until you've read the others |
| 17 | `src/naaptol/pipeline.py` | 100 | Ties it all together. Read it last and the whole system clicks |
| 18 | `app.py` | 364 | The Streamlit screen. Mostly layout |

Two files you can skip for now: `report.py` (makes the PDF) and `store.py` (saves to a database). Neither affects how compliance is decided.

**Then read the tests** — `tests/test_geometry.py` first, it is the shortest. Tests are worked examples with the expected answer written next to them, which makes them one of the fastest ways to understand code.

### Day 4 — The presentation (about 2 hours)

| # | Read | Why |
|---|---|---|
| 19 | `docs/03-presentation-guide.md` | Slide-by-slide content, what to say out loud, questions judges ask |
| 20 | `docs/SIH26034-Idea-Submission.pptx` | The 5-slide portal submission. Fill in your team's names |
| 21 | `docs/SIH26034-Demo-Deck.pptx` | The 9-slide deck for the live demo, with real screenshots |

### Reference — read when the question comes up

| File | Read it when |
|---|---|
| `docs/04-licensing-and-tooling.md` | Someone asks what this costs, or which licences apply. Short answer: nothing, everything is free and open source |
| `docs/01-problem-analysis.md` | You want the deep version — full legal analysis, the architecture a professional team would build |
| `scripts/make_sample_labels.py` | You want to add new test labels |
| `scripts/benchmark.py` | You want to measure accuracy |

> ⚠️ **About `01-problem-analysis.md`:** it describes an ambitious system that would take a professional team months. **It is not what you are expected to build.** It is there so you can answer "where could this go next?" Read it for the vision, follow `02-project-roadmap.md` for the work.

---

## The five ideas that matter

If you understand these five things, you understand the project.

**1. This is a measuring problem, not a reading problem.**
Rule 7 sets minimum letter heights of 1.0 to 6.0 mm depending on how big the front of the pack is. Software that only reads text can tell you the price is printed. It cannot tell you the price is printed 0.4 mm too small — and that is itself the offence. *(See `geometry.py`.)*

**2. A card of known size turns pixels into millimetres.**
Put a 50 mm printed marker in the photo. The software finds it, sees it measures 600 pixels across, and now knows 1 pixel = 0.083 mm. Every measurement follows from that. *(See `scale.py`.)*

**3. The system never guesses a violation.**
Bad photo, missing card, or a reading that sits right on the threshold, and the answer is **NEEDS PHYSICAL CHECK** — never FAIL. A wrong accusation against an honest shopkeeper is a worse outcome than a missed case. *(See `quality.py` and the `height_verdict` function in `geometry.py`.)*

**4. The rules are data, not code.**
They live in `config/rules/lmpc-2011.json`. A Legal Metrology officer could edit that file without a programmer. Each rule also carries valid-from dates, so a packet is judged by the rules in force when it was packed — which matters, because the rules changed in 2021, 2022, 2023, 2025 and 2026.

**5. Every answer cites its rule.**
Never just "non-compliant", but *"FAIL — Rule 7(2), Table-I: measured 1.92 mm, required 2.5 mm for a 108 cm² panel."* An officer can attach that to a real case file.

---

## Words you'll meet

| Word | What it means |
|---|---|
| **Legal Metrology** | The law of measurement in trade. "Metrology" is just the science of measurement |
| **LMPC Rules** | Legal Metrology (Packaged Commodities) Rules, 2011 — the rulebook this project checks against |
| **Declaration** | One of the nine things a packet must print (price, net quantity, manufacturer, and so on) |
| **PDP** | Principal Display Panel — the main front face of the pack. Its area decides the required letter height |
| **MRP** | Maximum Retail Price. Must be printed with the words "inclusive of all taxes" |
| **OCR** | Optical Character Recognition — software that reads text out of an image |
| **ArUco marker** | The black-and-white square pattern on the reference card. Software finds it easily and it has a known real-world size |
| **mm per pixel** | The scale. How many millimetres one pixel represents. Everything depends on this |
| **Rectify** | Digitally flatten a photo taken at an angle, so measurements aren't distorted |
| **INDETERMINATE** | "I cannot tell from this image." A first-class answer in this system, not an error |
| **Rule pack** | The JSON file holding the encoded rules |
| **Ground truth** | The real, known answer, used to check whether the software is right |

---

## Your first week

- [ ] Check the real deadline on sih.gov.in
- [ ] Read Day 1 and Day 2 above
- [ ] Get the app running on your own laptop
- [ ] Print the reference card at **exactly 50 mm** and check it with a ruler
- [ ] Photograph 5 real packets from a shop, with the card beside them, and scan them
- [ ] Write down what worked and what didn't — real photos are harder than our test labels, and finding out how much harder is genuinely useful
- [ ] Read Day 3 and pick which part of the code you want to own

---

## The most valuable thing you could do next

Every accuracy number in this repository comes from **synthetic labels** — images the computer drew itself, where the true letter height is known exactly. Those numbers prove the maths is right. They prove nothing about real photographs of real packets.

So: buy or borrow a **vernier caliper** (₹200–600, or the mechanical lab has one). Photograph 20 real packets. Measure the MRP letter height on each by hand. Compare.

That single afternoon converts every claim in the presentation from *"we think"* to *"we measured"*. No other task comes close in value, and no other team will have done it.

---

## If you get stuck

1. `docs/05-running-the-demo.md` has a troubleshooting table for the common problems
2. Every code file starts with a comment explaining what it does and why
3. The tests are worked examples — `tests/test_geometry.py` is the friendliest place to look
4. Ask. Being stuck for two days on something someone could explain in five minutes is the most common way hackathon time gets lost

---

## What you are not expected to do

- Understand every line of the code. Own one part well
- Build everything in `01-problem-analysis.md`. That's the ten-year vision
- Get real photographs working perfectly. Getting them working *at all*, and reporting honestly how well, is already ahead of most teams
- Know the law by heart. Know the nine declarations and the Rule 7 height table; look up the rest

Good luck. The idea is strong and the code already works — the remaining work is proving it on real packets and telling the story clearly.
