"""Produce the evidence document an officer can attach to a case file.

The point of this module is not pretty output. It is that every number on the
page can be traced back: which rule, which image, which rule-pack version,
which scale method, and what the measurement uncertainty was.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import cv2
from fpdf import FPDF

from .models import BORDERLINE, FAIL, INDETERMINATE, NOT_APPLICABLE, PASS, ScanResult

NAVY = (30, 39, 97)
GREY = (90, 100, 128)
RED = (192, 57, 43)
GREEN = (44, 138, 90)
AMBER = (217, 154, 32)
LIGHT = (238, 242, 251)

VERDICT_COLOUR = {
    PASS: GREEN, FAIL: RED, BORDERLINE: AMBER,
    INDETERMINATE: GREY, NOT_APPLICABLE: (150, 150, 150),
}


class _Pdf(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*GREY)
        self.cell(0, 5, "NAAP-TOL  |  LEGAL METROLOGY COMPLIANCE REPORT", align="L")
        self.ln(7)

    def footer(self):
        self.set_y(-14)
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*GREY)
        self.multi_cell(
            0, 3.5,
            "Advisory only. This report is decision support for a Legal Metrology "
            "officer, not an adjudication. Verify against the bare Act and Rules "
            "before any enforcement action.    Page " + str(self.page_no()),
            align="L",
        )


def _clean(text: str) -> str:
    """fpdf2's core fonts are Latin-1 only; drop what they cannot encode."""
    return (text or "").encode("latin-1", "replace").decode("latin-1")


def build_pdf(result: ScanResult, out_path: str | Path,
              annotated_image=None) -> Path:
    out_path = Path(out_path)
    pdf = _Pdf(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # -- headline ---------------------------------------------------------
    overall = result.overall
    colour = {"COMPLIANT": GREEN, "NON-COMPLIANT": RED}.get(overall, AMBER)

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 9, "Compliance Report", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*colour)
    pdf.cell(0, 8, _clean(overall), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    # -- provenance -------------------------------------------------------
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*GREY)
    rows = [
        ("Scanned at", result.scanned_at or "-"),
        ("Rule pack", f"LMPC-2011 v{result.rule_pack_version}"),
        ("Package type", result.context.package_type),
        ("Panel area",
         f"{result.context.pdp_area_cm2:.1f} cm2" if result.context.pdp_area_cm2 else "not supplied"),
        ("Scale method", f"{result.scale.method} ({result.scale.grade} grade)"),
        ("Scale",
         f"1 px = {result.scale.mm_per_px:.4f} mm  +/- {result.scale.rel_uncertainty * 100:.1f} %"
         if result.scale.usable else "not established"),
        ("Capture quality",
         f"{result.quality.grade} (focus {result.quality.focus:.2f}, "
         f"OCR confidence {result.quality.ocr_confidence:.0%})" if result.quality else "-"),
        ("Image SHA-256", (result.image_sha256 or "-")[:48]),
    ]
    for key, value in rows:
        pdf.cell(34, 4.6, _clean(key))
        pdf.set_text_color(20, 20, 20)
        pdf.cell(0, 4.6, _clean(str(value)), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*GREY)
    pdf.ln(3)

    # -- annotated evidence image ----------------------------------------
    if annotated_image is not None:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
            cv2.imwrite(handle.name, annotated_image)
            temp = handle.name
        available = pdf.w - 2 * pdf.l_margin
        pdf.image(temp, w=min(available, 150))
        Path(temp).unlink(missing_ok=True)
        pdf.ln(3)

    # -- findings ---------------------------------------------------------
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 7, "Findings", new_x="LMARGIN", new_y="NEXT")

    for finding in result.findings:
        if finding.verdict == NOT_APPLICABLE:
            continue
        _finding_block(pdf, finding)

    skipped = [f for f in result.findings if f.verdict == NOT_APPLICABLE]
    if skipped:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*GREY)
        pdf.cell(0, 5, "Not applicable to this package", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        for finding in skipped:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 4,
                           _clean(f"  {finding.citation} - {finding.title}: {finding.reason}"))

    pdf.output(str(out_path))
    return out_path


def _finding_block(pdf: FPDF, finding) -> None:
    colour = VERDICT_COLOUR.get(finding.verdict, GREY)

    pdf.ln(1.5)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*colour)
    pdf.cell(30, 5, _clean(finding.verdict))
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 5, _clean(f"{finding.citation}  -  {finding.title}"),
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(30, 30, 30)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 4.2, _clean(finding.reason))

    if finding.measured or finding.required:
        pdf.set_text_color(*GREY)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 4.2, _clean(
            f"    measured {finding.measured or '-'}   required {finding.required or '-'}"
        ))

    if finding.verdict in (FAIL, BORDERLINE) and finding.remedy:
        pdf.set_text_color(*GREY)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 4.2, _clean(f"    Remedy: {finding.remedy}"))
        if finding.exposure:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 4.2, _clean(f"    Exposure: {finding.exposure}"))
