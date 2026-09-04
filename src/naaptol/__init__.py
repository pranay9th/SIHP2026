"""Naap-Tol: Legal Metrology compliance checking by measurement.

SIH26034, Ministry of Consumer Affairs, Food & Public Distribution.

The design rests on one idea: the Legal Metrology (Packaged Commodities)
Rules, 2011 are a MEASUREMENT law. Rule 7 sets minimum letter heights in
millimetres, keyed to the computed area of the pack's principal display panel.
Reading the text off a label cannot detect an under-height declaration, and an
under-height declaration is itself the offence.

Module map:

    scale      recover millimetres-per-pixel; rectify the photograph
    geometry   Rule 7 panel area and the letter-height table
    ocr        text recognition behind a swappable backend interface
    quality    decide whether a photograph can support a conclusion at all
    extract    pattern-match the nine declarations out of OCR output
    rules      the rule engine; rules are data, loaded from JSON
    pipeline   scan() ties it all together
    report     the evidence PDF an officer can attach to a case file
    store      SQLite history and the repeat-offender ledger

The safety property the whole design rests on: the system never manufactures
a violation. Missing scale, unknown panel area, an indicative-only scale, a
borderline reading or a poor photograph all produce INDETERMINATE, not FAIL.
"""

__version__ = "0.1.0"
__all__ = [
    "extract", "geometry", "models", "ocr", "pipeline",
    "quality", "report", "rules", "scale", "store",
]
