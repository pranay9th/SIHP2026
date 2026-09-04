# Licensing, Tooling and Access

**SIH26034 — Naap-Tol**
What must be paid for, what is free, and what to say if a judge asks.

---

## The short answer

> **Nothing in this project requires a purchase, a subscription, a licence fee, or a government approval.**
> Every component is free and open source. Total cost to build and demonstrate: **₹0**, plus about ₹5 to print the reference card on a sheet of paper.

That is not an accident, it is a design decision, and it is worth saying out loud in the presentation. A government tool that depends on a paid cloud API has a recurring bill attached to every scan, in every district, forever. This one runs on a laptop.

---

## 1. Software licences — what is actually in the build

Every library below ships under a permissive open-source licence. None requires payment, registration, or an account.

| Component | Version used | Licence | Cost | Commercial use | Notes |
|---|---|---|---|---|---|
| **Python** | 3.11 | PSF License | Free | Yes | — |
| **OpenCV** (`opencv-python`) | 4.13 | Apache 2.0 | Free | Yes | ArUco moved into the main `objdetect` module at 4.7, so `opencv-contrib` is **not** needed |
| **NumPy** | 2.x | BSD-3-Clause | Free | Yes | — |
| **Pillow** | 12.x | MIT-CMU | Free | Yes | Used by the label generator |
| **Streamlit** | 1.x | Apache 2.0 | Free | Yes | Self-hosted; no account needed to run locally |
| **pandas** | 2.x | BSD-3-Clause | Free | Yes | — |
| **Plotly** | 5.x | MIT | Free | Yes | — |
| **SQLite** | bundled | **Public domain** | Free | Yes | Built into Python |
| **pytest** | 8.x | MIT | Free | Yes | Development only |
| **Tesseract OCR** | 5.3 | Apache 2.0 | Free | Yes | Default OCR engine |
| **pytesseract** | 0.3.x | Apache 2.0 | Free | Yes | Thin wrapper |
| **EasyOCR** | 1.7 | Apache 2.0 | Free | Yes | Optional; better Hindi. Pulls in PyTorch (BSD-3) |
| **PaddleOCR** | 2.x | Apache 2.0 | Free | Yes | Optional alternative |
| **fpdf2** | 2.x | **LGPL-3.0** | Free | Yes | ⚠️ see note below |

### ⚠️ The one licence worth understanding: fpdf2 is LGPL

`fpdf2` is the only component that is **not** permissively licensed. LGPL-3.0 is still free and still fine for this project — you may use it commercially, and simply importing it as a library does not oblige you to open-source your own code. The obligation only bites if you distribute a modified fpdf2, or statically link it into a closed binary.

**For a hackathon this is a non-issue.** If a judge asks, or if the project were ever commercialised as closed-source, swap it:

| Instead of | Use | Licence |
|---|---|---|
| fpdf2 (LGPL-3.0) | **ReportLab** (open-source toolkit) | BSD-3-Clause |
| fpdf2 | **WeasyPrint** (HTML → PDF) | BSD-3-Clause |

The change touches one file, `src/naaptol/report.py`.

### Licence summary for a slide

> 13 of 14 components are permissively licensed (Apache 2.0, BSD, MIT, PSF, or public domain). One, the PDF writer, is LGPL, which imposes no obligation on our code and has a BSD drop-in replacement if ever needed.

---

## 2. Things people assume you need — and how this project avoids them

This is the table to have ready. Judges often assume a vision project must be renting a cloud API.

| Commonly assumed | Typical cost | Do we need it? | What we do instead |
|---|---|---|---|
| Google Cloud Vision API | ~$1.50 / 1000 images | **No** | Tesseract or EasyOCR, locally |
| Azure AI Vision / AWS Textract | ~$1.00–1.50 / 1000 | **No** | Same |
| OpenAI / Gemini / Claude API for reading labels | per-token billing | **No** | Regex extraction — and it is *more* explainable to an officer, not less |
| Google Maps Platform (heatmaps) | pay-per-load after free tier | **No** | Plotly, or Folium with OpenStreetMap tiles |
| A GPU | ₹40k+, or cloud rental | **No** | Tesseract is CPU-only; EasyOCR runs CPU-only with `gpu=False` |
| Paid OCR SDK (ABBYY etc.) | licence per seat | **No** | Open-source OCR |
| Cloud hosting | ₹500+/month | **No for the demo** | Runs on a laptop; Streamlit Community Cloud is free if you want a public link |
| Domain name | ~₹800/year | **No** | Not needed |
| Play Store developer account | $25 one-time | **No** | Mobile-friendly web app, not a native app |
| Database server licence | varies | **No** | SQLite, public domain, zero install |
| Figma / Canva Pro | subscription | **No** | Free tiers are ample |
| GitHub | — | **No** | Free for public and private repos |

**If asked "what would this cost the government to run at scale?"**: the honest answer is servers and support, not licences. There are no per-scan fees and no vendor lock-in, because there is no vendor.

---

## 3. Physical items you need to buy

| Item | Cost | Why |
|---|---|---|
| A4 paper + laser/inkjet print of the reference card | ~₹5 | The ArUco marker must print at **exactly 50 mm**. Print at 100 % scale, never "fit to page", then check with a ruler. |
| Vernier caliper *(strongly recommended)* | ₹200–600, or borrow from the mechanical lab | To hand-measure real labels and produce a ground-truth accuracy figure. **This is the single most valuable ₹300 you can spend on this project** — it turns an unverifiable claim into a measured one. |
| A few retail packets from a local shop | ₹500 total | Your real test set |
| A phone with a camera | already owned | — |

**Total: under ₹1,200**, and most of it optional.

---

## 4. Legal permissions — is any government licence or approval needed?

No, and this matters because the domain sounds regulated.

| Question | Answer |
|---|---|
| Do we need a Legal Metrology licence to build this? | **No.** Licences under the Act are for *manufacturers, packers, importers and dealers of weights and measures* — people who trade using measuring instruments. Writing software that reads labels is not a regulated activity. |
| Can we reproduce the text of the Rules in our app? | **Yes.** Indian statutes, rules and government notifications are published for public use. Cite them properly — we do, on every finding. |
| Can we photograph branded retail packets? | **Yes**, for study, testing and demonstration. Be careful about *publishing* a public list naming brands as violators — that is a reputational claim you cannot support from a student project. In the demo, either use your own synthetic labels or blur brand marks. |
| Can we scrape Amazon or Flipkart listings? | **No — do not.** It breaches their terms of use and is an unforced legal risk in a government-facing project. Use seller-provided feeds, official APIs, or user-submitted screenshots. If a judge asks about the e-commerce lane, say exactly that. |
| Does our output have legal force? | **No,** and the system says so. Every report carries: *"Advisory only. Decision support for a Legal Metrology officer, not an adjudication."* Never claim otherwise. |
| Any data-protection concern? | Minimal. The system stores label photographs and scan results, not personal data. If a consumer-reporting feature is ever added, that changes — flag it as future work with a DPDP Act note. |

---

## 5. Accounts to create — all free

| Account | Needed for | Cost |
|---|---|---|
| GitHub | Code hosting, and judges may ask for a repo link | Free |
| Streamlit Community Cloud | *Optional* public demo link | Free |
| SIH portal (sih.gov.in) | Registration and idea submission | Free |

Nothing else. No cloud provider, no API key, no credit card.

---

## 6. What to say in the presentation

Put this on the Feasibility slide:

> **Zero licence cost.** Every component is open source under Apache 2.0, BSD, MIT or public domain. No paid API, no GPU, no cloud subscription, no vendor lock-in. The system runs offline on a standard laptop — which matters, because the officers who would use it work in markets without reliable connectivity.

And keep this ready for questions:

**"Why not use Google Vision or GPT for the OCR? It would be more accurate."**
> Three reasons. Cost — a per-image fee across lakhs of shops is a permanent bill on a public system. Connectivity — inspectors work where there is no signal, and our pipeline runs entirely offline. And explainability — an officer has to defend a finding, so a regex that matches a printed phrase can be shown in court in a way a model's output cannot. We kept the OCR engine behind an interface, so a better engine can be swapped in with one line if a state ever wants to.

**"What happens when this needs to scale nationally?"**
> The cost is servers and support, not licences. Nothing here charges per scan.

---

## 7. Installing everything

```bash
# One command. No accounts, no keys.
pip install -r requirements.txt

# Tesseract is a system package, not a Python one:
#   Ubuntu / Debian :  sudo apt install tesseract-ocr tesseract-ocr-hin
#   macOS           :  brew install tesseract tesseract-lang
#   Windows         :  https://github.com/UB-Mannheim/tesseract/wiki
```

Then:

```bash
python scripts/make_sample_labels.py   # generate test labels + reference card
python scripts/seed_demo_data.py       # fill the dashboard
python -m pytest tests/ -q             # 53 tests
python scripts/benchmark.py --robustness
streamlit run app.py
```

---

## Sources

- Component licences taken from each project's own repository and PyPI metadata
- [Legal Metrology Act, 2009](https://lawgist.in/legal-metrology-act/36) — Section 36 penalties; licensing provisions apply to traders in weights and measures, not to software
- [Legal Metrology (Packaged Commodities) Rules, 2011](https://legalmetrologymh.in/public/temp/368/02d3c4fef3045bc21d90ba000a28357e.pdf)
