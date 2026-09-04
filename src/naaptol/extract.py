"""Turn messy OCR output into the nine declarations, using pattern matching.

No machine learning here on purpose. Label declarations are highly formulaic,
regular expressions handle them well, and every match is explainable to an
officer, which a neural extractor is not.
"""
from __future__ import annotations

import re

from .models import LabelFacts, TextBox

# --------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------

# "Rs.40", "Rs 40.50", "MRP 40", "INR 40", the rupee sign, "₹40"
_PRICE = r"(?:rs\.?|inr|mrp|₹)\s*\.?\s*(\d+(?:[.,]\d{1,2})?)"

RE_MRP = re.compile(
    r"(?:m\.?r\.?p\.?|maximum\s+retail\s+price|retail\s+sale\s+price)?"
    r"[^\n]{0,30}?" + _PRICE,
    re.I,
)
RE_PRICE_ONLY = re.compile(_PRICE, re.I)

RE_INCLUSIVE = re.compile(r"inclusive\s+of\s+all\s+taxes", re.I)

RE_NET_QTY = re.compile(
    r"(?:net\s*(?:wt\.?|weight|qty\.?|quantity|vol\.?|volume|content[s]?)\s*"
    r"[:.\-]?\s*)?"
    r"(\d+(?:\.\d+)?)\s*"
    r"(kg|kgs|g|gm|gms|gram[s]?|mg|l|lt|ltr|litre[s]?|liter[s]?|ml|n|no\.?|pcs?|piece[s]?|u)\b",
    re.I,
)
RE_NET_QTY_LABELLED = re.compile(
    r"net\s*(?:wt\.?|weight|qty\.?|quantity|vol\.?|volume|content[s]?)\s*[:.\-]?\s*"
    r"(\d+(?:\.\d+)?)\s*"
    r"(kg|kgs|g|gm|gms|gram[s]?|mg|l|lt|ltr|litre[s]?|liter[s]?|ml|n|no\.?|pcs?|piece[s]?|u)\b",
    re.I,
)

RE_MFG_DATE = re.compile(
    r"(?:mfg\.?|mfd\.?|manufactured|packed|pkd\.?|date\s+of\s+(?:mfg|packing)|"
    r"month\s+and\s+year)"
    r"[^\n]{0,20}?"
    r"((?:\d{1,2}[/\-.])?(?:\d{1,2}|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
    r"[a-z]*[/\-.\s]\d{2,4})",
    re.I,
)

RE_BEST_BEFORE = re.compile(
    r"(?:best\s+before|use\s+by|expiry|exp\.?|consume\s+before)"
    r"[^\n]{0,40}",
    re.I,
)

RE_MANUFACTURER = re.compile(
    r"(?:manufactured\s+by|mfd\.?\s+by|mfg\.?\s+by|packed\s+by|marketed\s+by|"
    r"imported\s+by|name\s+and\s+address)"
    r"\s*[:.\-]?\s*([^\n]{4,120})",
    re.I,
)

RE_COUNTRY = re.compile(
    r"country\s+of\s+origin\s*[:.\-]?\s*([A-Za-z][A-Za-z .\-]{2,40})",
    re.I,
)

RE_CONSUMER_CARE = re.compile(
    r"(?:consumer\s+care|customer\s+care|for\s+(?:any\s+)?(?:complaint|queries|"
    r"grievance)[s]?|grievance\s+officer|contact\s+us)"
    r"[^\n]{0,120}",
    re.I,
)
RE_PHONE = re.compile(r"(?:\+91[\-\s]?)?(?:1800[\-\s]?\d{3}[\-\s]?\d{3,4}|\b\d{10}\b)")
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

RE_COMMON_NAME = re.compile(
    r"(?:common\s+name|generic\s+name|product\s+name|commodity)\s*[:.\-]?\s*"
    r"([^\n]{2,60})",
    re.I,
)

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_LATIN = re.compile(r"[A-Za-z]")

_UNIT_CANON = {
    "kg": "kg", "kgs": "kg",
    "g": "g", "gm": "g", "gms": "g", "gram": "g", "grams": "g",
    "mg": "mg",
    "l": "l", "lt": "l", "ltr": "l", "litre": "l", "litres": "l",
    "liter": "l", "liters": "l",
    "ml": "ml",
    "n": "n", "no": "n", "no.": "n", "pc": "n", "pcs": "n",
    "piece": "n", "pieces": "n", "u": "n",
}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def boxes_to_text(boxes: list[TextBox]) -> str:
    """Rebuild reading-order text from boxes, grouping into lines.

    Boxes whose vertical centres are close are treated as one line, then sorted
    left to right. Without this, OCR output order alone breaks multi-column
    labels and the context patterns stop matching.
    """
    if not boxes:
        return ""

    items = [(b, b.bbox[1] + b.bbox[3] / 2.0) for b in boxes]
    items.sort(key=lambda t: t[1])

    median_h = sorted(b.bbox[3] for b in boxes)[len(boxes) // 2] or 10
    tolerance = max(6.0, median_h * 0.6)

    lines: list[list[TextBox]] = []
    current: list[TextBox] = []
    current_y: float | None = None

    for box, cy in items:
        if current_y is None or abs(cy - current_y) <= tolerance:
            current.append(box)
            current_y = cy if current_y is None else (current_y + cy) / 2.0
        else:
            lines.append(current)
            current, current_y = [box], cy
    if current:
        lines.append(current)

    out = []
    for line in lines:
        line.sort(key=lambda b: b.bbox[0])
        out.append(" ".join(b.text for b in line))
    return "\n".join(out)


def find_box_for(boxes: list[TextBox], needle: str) -> TextBox | None:
    """Find the box whose text best carries ``needle`` (e.g. the MRP digits)."""
    needle = needle.strip().lower()
    if not needle:
        return None

    exact = [b for b in boxes if b.text.strip().lower() == needle]
    if exact:
        return max(exact, key=lambda b: b.bbox[3])

    contains = [b for b in boxes if needle in b.text.strip().lower()]
    if contains:
        return min(contains, key=lambda b: len(b.text))

    digits = re.sub(r"[^\d.]", "", needle)
    if digits:
        for b in boxes:
            if digits in re.sub(r"[^\d.]", "", b.text):
                return b
    return None


def _context(text: str, match: re.Match, window: int = 90) -> str:
    start = max(0, match.start() - window)
    end = min(len(text), match.end() + window)
    return text[start:end].replace("\n", " ")


def _canon_unit(raw: str) -> str | None:
    return _UNIT_CANON.get(raw.strip().lower().rstrip("."))


def dominant_script(text: str) -> str:
    if _DEVANAGARI.search(text):
        return "devanagari" if not _LATIN.search(text) else "mixed"
    if _LATIN.search(text):
        return "latin"
    return "unknown"


# --------------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------------

def extract(boxes: list[TextBox], raw_text: str | None = None) -> LabelFacts:
    """Pull the declarations out of OCR output."""
    text = raw_text if raw_text is not None else boxes_to_text(boxes)
    facts = LabelFacts(raw_text=text, boxes=list(boxes))

    # -- retail sale price ------------------------------------------------
    m = RE_MRP.search(text) or RE_PRICE_ONLY.search(text)
    if m:
        facts.mrp = m.group(0).strip()
        facts.mrp_context = _context(text, m)
        try:
            facts.mrp_value = float(m.group(1).replace(",", "."))
        except (ValueError, IndexError):
            facts.mrp_value = None
        box = find_box_for(boxes, m.group(1) if m.lastindex else m.group(0))
        if box:
            facts.measured_boxes["mrp"] = box

    # -- net quantity -----------------------------------------------------
    m = RE_NET_QTY_LABELLED.search(text) or RE_NET_QTY.search(text)
    if m:
        facts.net_quantity = m.group(0).strip()
        facts.net_quantity_context = _context(text, m)
        try:
            facts.net_quantity_value = float(m.group(1))
        except (ValueError, IndexError):
            facts.net_quantity_value = None
        facts.net_quantity_unit = _canon_unit(m.group(2))
        box = find_box_for(boxes, m.group(1))
        if box:
            facts.measured_boxes["net_quantity"] = box

    # -- dates ------------------------------------------------------------
    m = RE_MFG_DATE.search(text)
    if m:
        facts.mfg_date = m.group(0).strip()

    m = RE_BEST_BEFORE.search(text)
    if m:
        facts.best_before = m.group(0).strip()

    # -- manufacturer and origin ------------------------------------------
    m = RE_MANUFACTURER.search(text)
    if m:
        facts.manufacturer = m.group(1).strip()

    m = RE_COUNTRY.search(text)
    if m:
        facts.country_of_origin = m.group(1).strip()

    # -- consumer care ----------------------------------------------------
    m = RE_CONSUMER_CARE.search(text)
    if m:
        facts.consumer_care = m.group(0).strip()
    elif RE_PHONE.search(text) or RE_EMAIL.search(text):
        hit = RE_PHONE.search(text) or RE_EMAIL.search(text)
        facts.consumer_care = hit.group(0).strip()

    # -- common name ------------------------------------------------------
    m = RE_COMMON_NAME.search(text)
    if m:
        facts.common_name = m.group(1).strip()
    else:
        # Fall back to the largest text on the pack, which is nearly always the
        # product name. Word-level OCR splits that name across several boxes, so
        # take the tallest box and then gather the whole line it sits on;
        # otherwise "Crisp Salted Biscuits" comes back as just "Crisp".
        candidates = [
            b for b in boxes
            if len(b.text.strip()) >= 3 and not RE_PRICE_ONLY.search(b.text)
        ]
        if candidates:
            tallest = max(candidates, key=lambda b: b.bbox[3])
            centre = tallest.bbox[1] + tallest.bbox[3] / 2.0
            tolerance = max(4.0, tallest.bbox[3] * 0.5)
            line = [
                b for b in boxes
                if abs((b.bbox[1] + b.bbox[3] / 2.0) - centre) <= tolerance
                and b.bbox[3] >= tallest.bbox[3] * 0.6
            ]
            line.sort(key=lambda b: b.bbox[0])
            facts.common_name = " ".join(b.text.strip() for b in line).strip()

    return facts
