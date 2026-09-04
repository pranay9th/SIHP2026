"""Naap-Tol demo application.

Run it with:

    streamlit run app.py

Three tabs: scan a package, see the enforcement dashboard, read the rule pack.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from naaptol import geometry, ocr, pipeline, report, store  # noqa: E402
from naaptol.models import (  # noqa: E402
    BORDERLINE, FAIL, INDETERMINATE, NOT_APPLICABLE, PASS, PackageContext,
)
from naaptol.rules import RulePack  # noqa: E402

st.set_page_config(page_title="Naap-Tol", page_icon="",
                   layout="wide", initial_sidebar_state="expanded")

BADGE = {
    PASS: ("PASS", "#2C8A5A"),
    FAIL: ("FAIL", "#C0392B"),
    BORDERLINE: ("BORDERLINE", "#D99A20"),
    INDETERMINATE: ("NEEDS CHECK", "#5A6480"),
    NOT_APPLICABLE: ("N/A", "#9AA3B8"),
}

st.markdown("""
<style>
  .block-container { padding-top: 2.2rem; max-width: 1400px; }
  .verdict-big { font-size: 1.6rem; font-weight: 700; letter-spacing: .3px; }
  .finding { border:1px solid #E2E7F2; border-radius:8px; padding:10px 14px;
             margin-bottom:8px; background:#fff; }
  .badge { display:inline-block; color:#fff; font-size:.68rem; font-weight:700;
           padding:2px 8px; border-radius:10px; letter-spacing:.5px; }
  .cite { color:#5A6480; font-size:.78rem; }
  .muted { color:#5A6480; font-size:.85rem; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_rule_pack():
    return RulePack.load()


@st.cache_resource
def get_backend(name: str):
    return ocr.get_backend(name)


@st.cache_resource
def get_db():
    return store.connect()


def sample_files() -> list[Path]:
    return sorted((ROOT / "data" / "samples").glob("*.png"))


# ==========================================================================
# Sidebar: everything the rule engine needs to know about the package
# ==========================================================================

st.sidebar.title("Naap-Tol")
st.sidebar.caption("Legal Metrology compliance by measurement")

try:
    backend_choice = st.sidebar.selectbox(
        "OCR engine", ["auto", "tesseract", "easyocr", "paddleocr"], index=0
    )
    backend = get_backend(backend_choice)
    st.sidebar.success(f"OCR: {backend.name}")
except Exception as exc:  # noqa: BLE001
    backend = None
    st.sidebar.error(str(exc))

st.sidebar.divider()
st.sidebar.subheader("Package details")

package_type = st.sidebar.selectbox("Package type", ["retail", "wholesale", "export"])
shape = st.sidebar.selectbox(
    "Pack shape", ["rectangular", "cylindrical", "other"],
    help="Rule 7(4) computes the panel area differently for each shape.",
)

if shape == "rectangular":
    col_a, col_b = st.sidebar.columns(2)
    panel_w = col_a.number_input("Panel width (mm)", 10.0, 2000.0, 120.0, 5.0)
    panel_h = col_b.number_input("Panel height (mm)", 10.0, 2000.0, 90.0, 5.0)
    pdp_area = geometry.pdp_area_cm2("rectangular", height_mm=panel_h, width_mm=panel_w)
elif shape == "cylindrical":
    col_a, col_b = st.sidebar.columns(2)
    cyl_h = col_a.number_input("Height (mm)", 10.0, 2000.0, 150.0, 5.0)
    cyl_d = col_b.number_input("Diameter (mm)", 5.0, 1000.0, 60.0, 5.0)
    pdp_area = geometry.pdp_area_cm2("cylindrical", height_mm=cyl_h, diameter_mm=cyl_d)
else:
    total = st.sidebar.number_input("Total surface area (cm2)", 1.0, 20000.0, 400.0, 10.0)
    pdp_area = geometry.pdp_area_cm2("other", total_surface_cm2=total)

surface_type = st.sidebar.selectbox(
    "Surface", ["normal", "blown"],
    help="Blown, formed, moulded or embossed containers get a larger minimum height.",
)
required_mm = geometry.required_letter_height_mm(
    pdp_area, get_rule_pack().bands, surface_type
)
st.sidebar.info(
    f"Panel area **{pdp_area:.1f} cm2**\n\n"
    f"Rule 7 minimum letter height **{required_mm:.1f} mm**"
)

net_qty = st.sidebar.number_input(
    "Net quantity (g or ml)", 0.0, 100000.0, 200.0, 10.0,
    help="Used for the Rule 26 exemption test (10 g/ml or less is exempt).",
)
is_imported = st.sidebar.checkbox("Imported package")
is_medical = st.sidebar.checkbox(
    "Medical device",
    help="The 2025 Amendment hands letter sizing to the Medical Devices Rules 2017.",
)
category = st.sidebar.selectbox(
    "Commodity category", ["general", "fast_food", "agricultural"]
)

st.sidebar.divider()
marker_mm = st.sidebar.number_input("Reference marker size (mm)", 10.0, 200.0, 50.0, 5.0)

st.sidebar.divider()
st.sidebar.subheader("Record keeping")
brand = st.sidebar.text_input("Brand", "")
product = st.sidebar.text_input("Product", "")
state = st.sidebar.text_input("State", "")
district = st.sidebar.text_input("District", "")


# ==========================================================================
# Tabs
# ==========================================================================

tab_scan, tab_dash, tab_rules = st.tabs(
    ["Scan a package", "Enforcement dashboard", "Rule pack"]
)

# --------------------------------------------------------------------------
with tab_scan:
    st.header("Scan a package")
    st.caption(
        "Photograph the pack with the printed ArUco reference card lying flat "
        "beside it, in the same plane, square on to the camera."
    )

    source = st.radio("Image source", ["Sample label", "Upload", "Camera"],
                      horizontal=True)
    image = None
    image_bytes = None

    if source == "Sample label":
        files = sample_files()
        if not files:
            st.warning("No samples yet. Run: python scripts/make_sample_labels.py")
        else:
            chosen = st.selectbox("Sample", files, format_func=lambda p: p.stem)
            image = cv2.imread(str(chosen))
            image_bytes = chosen.read_bytes()
    elif source == "Upload":
        upload = st.file_uploader("Label photograph", type=["png", "jpg", "jpeg"])
        if upload:
            image_bytes = upload.getvalue()
            image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    else:
        shot = st.camera_input("Take a photograph")
        if shot:
            image_bytes = shot.getvalue()
            image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)

    if image is not None and backend is not None:
        ctx = PackageContext(
            package_type=package_type,
            pdp_area_cm2=pdp_area,
            surface_type=surface_type,
            is_imported=is_imported,
            is_medical_device=is_medical,
            commodity_category=category,
            net_quantity_g_or_ml=net_qty,
        )

        with st.spinner("Rectifying, reading and adjudicating..."):
            result = pipeline.scan(
                image, ctx, backend=backend, rule_pack=get_rule_pack(),
                marker_mm=marker_mm, image_bytes=image_bytes,
            )
            annotated = pipeline.annotate(result.working_image, result)

        colour = {"COMPLIANT": "#2C8A5A", "NON-COMPLIANT": "#C0392B"}.get(
            result.overall, "#D99A20"
        )

        left, right = st.columns([1.05, 1])

        with left:
            st.markdown(
                f"<div class='verdict-big' style='color:{colour}'>{result.overall}</div>",
                unsafe_allow_html=True,
            )
            m1, m2, m3 = st.columns(3)
            m1.metric("Declarations found", f"{result.declarations_present} / 9")
            m2.metric("Failures", result.count(FAIL))
            m3.metric("Needs check",
                      result.count(INDETERMINATE) + result.count(BORDERLINE))

            quality = result.quality
            note = (f"Scale: <b>{result.scale.method}</b> "
                    f"({result.scale.grade} grade) &nbsp;|&nbsp; "
                    f"Capture: <b>{quality.grade}</b>")
            if result.scale.usable:
                note += f"  |  1 px = {result.scale.mm_per_px:.4f} mm"
            st.markdown(f"<div class='muted'>{note}</div>", unsafe_allow_html=True)
            if quality.grade != "good":
                st.warning(quality.notes)

            st.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB),
                     caption="Rectified image with measured declarations",
                     use_container_width=True)

        with right:
            st.subheader("Report card")
            show_na = st.checkbox("Show rules that do not apply", value=False)
            for finding in result.findings:
                if finding.verdict == NOT_APPLICABLE and not show_na:
                    continue
                label, badge_colour = BADGE[finding.verdict]
                extra = ""
                if finding.measured:
                    extra = (f"<div class='cite'>measured <b>{finding.measured}</b> "
                             f"&nbsp; required <b>{finding.required}</b></div>")
                st.markdown(
                    f"<div class='finding'>"
                    f"<span class='badge' style='background:{badge_colour}'>{label}</span> "
                    f"<b>{finding.title}</b>"
                    f"<div class='cite'>{finding.citation}</div>"
                    f"<div style='font-size:.86rem;margin-top:4px'>{finding.reason}</div>"
                    f"{extra}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if finding.verdict in (FAIL, BORDERLINE) and finding.remedy:
                    with st.expander("Remedy and exposure"):
                        st.write(finding.remedy)
                        st.caption(finding.exposure)

        st.divider()
        act_a, act_b = st.columns(2)

        with act_a:
            if st.button("Save this scan", use_container_width=True):
                conn = get_db()
                scan_id = store.save(conn, result, brand=brand, product=product,
                                     category=category, state=state, district=district)
                history = store.offence_history(conn, brand)
                st.success(f"Saved as scan #{scan_id}.")
                if brand and result.overall == "NON-COMPLIANT":
                    st.warning(
                        f"**{brand}** now has {history['prior']} recorded "
                        f"non-compliant scans. Treated as a **{history['stage']} "
                        f"offence** under Section 36: {history['exposure']}."
                    )

        with act_b:
            out = Path(tempfile.gettempdir()) / "naaptol-report.pdf"
            report.build_pdf(result, out, annotated_image=annotated)
            st.download_button("Download PDF evidence report",
                               out.read_bytes(), file_name="naaptol-report.pdf",
                               mime="application/pdf", use_container_width=True)

        with st.expander("Text read from the label"):
            st.code(result.facts.raw_text or "(nothing read)")

# --------------------------------------------------------------------------
with tab_dash:
    st.header("Enforcement dashboard")
    conn = get_db()
    data = store.summary(conn)

    if data["total"] == 0:
        st.info("No scans recorded yet. Scan a package and press Save.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Packages scanned", data["total"])
        c2.metric("Non-compliant", data["by_overall"].get("NON-COMPLIANT", 0))
        c3.metric("Needs physical check", data["by_overall"].get("NEEDS PHYSICAL CHECK", 0))
        c4.metric("Compliant", data["by_overall"].get("COMPLIANT", 0))

        st.subheader("Most breached rules")
        if data["top_rules"]:
            frame = pd.DataFrame(data["top_rules"])
            frame.columns = ["Citation", "Rule", "Failures"]
            st.bar_chart(frame.set_index("Citation")["Failures"])
            st.dataframe(frame, use_container_width=True, hide_index=True)

        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Repeat offenders")
            if data["by_brand"]:
                st.dataframe(pd.DataFrame(data["by_brand"]),
                             use_container_width=True, hide_index=True)
        with col_right:
            st.subheader("By state")
            if data["by_state"]:
                st.dataframe(pd.DataFrame(data["by_state"]),
                             use_container_width=True, hide_index=True)

        st.subheader("Recent scans")
        recent = pd.read_sql_query(
            "SELECT id, scanned_at, brand, product, overall, fail_count, "
            "scale_grade, quality_grade FROM scans ORDER BY id DESC LIMIT 50", conn
        )
        st.dataframe(recent, use_container_width=True, hide_index=True)

# --------------------------------------------------------------------------
with tab_rules:
    pack = get_rule_pack()
    st.header("Rule pack")
    st.caption(
        f"{pack.data['rule_pack']} v{pack.version} — "
        "rules are data, not code. Amend the JSON file, not the program."
    )
    st.warning(pack.data["disclaimer"])

    st.subheader("Rule 7, Table-I — minimum letter height")
    st.dataframe(pd.DataFrame([
        {
            "Panel area (cm2)": (f"up to {b['pdp_area_cm2_max']}"
                                 if b["pdp_area_cm2_max"] else "above 2500"),
            "Normal (mm)": b["min_height_mm"],
            "Blown or moulded (mm)": b["min_height_mm_blown"],
        } for b in pack.bands
    ]), use_container_width=True, hide_index=True)

    st.subheader(f"Encoded rules ({len(pack.rules)})")
    st.dataframe(pd.DataFrame([
        {
            "Citation": r["citation"], "Title": r["title"], "Kind": r["kind"],
            "Severity": r.get("severity", ""),
            "In force from": r.get("effective_from", ""),
            "Until": r.get("effective_to") or "current",
        } for r in pack.rules
    ]), use_container_width=True, hide_index=True)

    st.subheader("Exemptions, Rule 26")
    st.dataframe(pd.DataFrame(pack.data["exemptions"]),
                 use_container_width=True, hide_index=True)
