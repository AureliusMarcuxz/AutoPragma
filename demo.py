"""
AutoPragma — SWE.1 Interactive Demo
Run: py -m streamlit run demo.py
"""

import json
import sys
from pathlib import Path

import streamlit as st

# Allow imports from prototype root when launched from any cwd
sys.path.insert(0, str(Path(__file__).parent))

from swe1 import derive_swrs, load_syrs, validate
from swe1.derive import DERIV_FUNCTIONAL, DERIV_SAFETY_MECH, DERIV_CYBERSEC
from swe1.models import ASIL
from swe1.validate import finding_counts

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AutoPragma — SWE.1",
    page_icon="images/autopragma-logo.png" if Path("images/autopragma-logo.png").exists() else ":gear:",
    layout="wide",
)

SAMPLE_PATH = Path(__file__).parent / "sample_data" / "sys_requirements.json"

# ── ASIL styling ──────────────────────────────────────────────────────────────

ASIL_COLOR = {
    ASIL.D:  ("#7f0000", "#ffcccc"),
    ASIL.C:  ("#7f2000", "#ffe0cc"),
    ASIL.B:  ("#7f5000", "#fff3cc"),
    ASIL.A:  ("#4a5a00", "#f0f5cc"),
    ASIL.QM: ("#1a5a1a", "#e0f5e0"),
}

def asil_badge(asil: ASIL) -> str:
    fg, bg = ASIL_COLOR.get(asil, ("#333", "#eee"))
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:4px;font-weight:700;font-size:0.85em;">'
        f'{asil.value}</span>'
    )

def cybersec_badge() -> str:
    return (
        '<span style="background:#dde8ff;color:#003080;padding:2px 8px;'
        'border-radius:4px;font-weight:700;font-size:0.85em;">CYBERSEC</span>'
    )

_DERIV_BADGE_STYLE = {
    DERIV_FUNCTIONAL:  ("FUNCTIONAL",   "#e8f4fd", "#0a4a7a"),
    DERIV_SAFETY_MECH: ("SAFETY MECH",  "#fff3cc", "#7f5000"),
    DERIV_CYBERSEC:    ("CYBERSEC IMPL","#f3e8fd", "#5a0a7a"),
}

def derivation_badge(deriv_type: str) -> str:
    label, bg, fg = _DERIV_BADGE_STYLE.get(
        deriv_type, (deriv_type, "#eee", "#333")
    )
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:4px;font-weight:700;font-size:0.85em;">{label}</span>'
    )

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("AutoPragma")
    st.caption("ASPICE Process Automation Platform")
    st.divider()

    st.subheader("SWE.1 — Requirements Engineering")
    st.markdown(
        "Upload a System Requirements Specification (SyRS) JSON file "
        "exported from your ALM tool, or use the built-in sample."
    )

    input_mode = st.radio("Input source", ["Sample SyRS (VSC)", "Upload file"])

    uploaded = None
    if input_mode == "Upload file":
        uploaded = st.file_uploader("SyRS JSON file", type=["json"])

    st.divider()
    run = st.button("Run SWE.1 Analysis", type="primary", use_container_width=True)

    st.divider()
    st.caption("ASPICE CL3 | ISO 26262 | ISO/SAE 21434 | MISRA")

# ── Main area ─────────────────────────────────────────────────────────────────

st.markdown("## AutoPragma — SWE.1 Software Requirements Analysis")
st.markdown(
    "This pipeline ingests a system-level requirements specification, "
    "validates completeness and consistency, derives a draft software "
    "requirements specification, and evaluates the SWE.1 process gate."
)

if not run:
    st.info("Configure your input in the sidebar and click **Run SWE.1 Analysis**.")
    st.stop()

# ── Load input ────────────────────────────────────────────────────────────────

try:
    if input_mode == "Sample SyRS (VSC)":
        metadata, syrs_items = load_syrs(str(SAMPLE_PATH))
    else:
        if uploaded is None:
            st.error("Please upload a SyRS JSON file before running.")
            st.stop()
        raw = json.loads(uploaded.read().decode("utf-8"))
        tmp = Path("output/_upload_tmp.json")
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(raw), encoding="utf-8")
        metadata, syrs_items = load_syrs(str(tmp))
except Exception as exc:
    st.error(f"Failed to load SyRS: {exc}")
    st.stop()

# ── Process ───────────────────────────────────────────────────────────────────

findings   = validate(syrs_items)
swrs_items, links = derive_swrs(syrs_items, metadata.get("project_key", "PROJ"))
counts     = finding_counts(findings)
gate_pass  = counts["ERROR"] == 0

# ── 1. Metadata banner ────────────────────────────────────────────────────────

n_functional  = sum(1 for sw in swrs_items if sw.derivation_type == DERIV_FUNCTIONAL)
n_safety_mech = sum(1 for sw in swrs_items if sw.derivation_type == DERIV_SAFETY_MECH)
n_cybersec    = sum(1 for sw in swrs_items if sw.derivation_type == DERIV_CYBERSEC)

st.divider()
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Document",       metadata.get("document_id", "—"))
c2.metric("Version",        metadata.get("version", "—"))
c3.metric("Status",         metadata.get("status", "—").upper())
c4.metric("SyRS Items",     len(syrs_items))
c5.metric("SwRS Generated", len(swrs_items))

d1, d2, d3 = st.columns(3)
d1.metric("Functional",       n_functional)
d2.metric("Safety Mechanism", n_safety_mech)
d3.metric("Cybersec Impl",    n_cybersec)

# ── 2. Gate result ────────────────────────────────────────────────────────────

st.divider()
if gate_pass:
    st.success("### SWE.1 Gate: PASS", icon="✅")
    st.markdown("No blocking errors. Draft software requirements are ready for review.")
else:
    st.error("### SWE.1 Gate: FAIL", icon="🚫")
    st.markdown(
        f"**{counts['ERROR']} error(s)** must be resolved before this work product "
        "can be baselined."
    )

# ── 3. Validation results ─────────────────────────────────────────────────────

st.divider()
st.subheader("Validation Results")

vcol1, vcol2, vcol3 = st.columns(3)
vcol1.metric("Errors",   counts["ERROR"],         delta=None)
vcol2.metric("Warnings", counts["WARNING"],       delta=None)
vcol3.metric("Info",     counts.get("INFO", 0),   delta=None)

if findings:
    errors   = [f for f in findings if f.severity == "ERROR"]
    warnings = [f for f in findings if f.severity == "WARNING"]

    if errors:
        with st.expander(f"Errors ({len(errors)})", expanded=True):
            for f in errors:
                st.error(f"**[{f.rule_id}]** `{f.item_id}` — {f.message}")

    if warnings:
        with st.expander(f"Warnings ({len(warnings)})", expanded=False):
            for f in warnings:
                st.warning(f"**[{f.rule_id}]** `{f.item_id}` — {f.message}")
else:
    st.success("All completeness and consistency checks passed.")

# ── 4. Traceability matrix ────────────────────────────────────────────────────

st.divider()
st.subheader("Traceability Matrix — SyRS to SwRS")

# Build a combined table
import pandas as pd

_DERIV_LABEL = {
    DERIV_FUNCTIONAL:  "FUNCTIONAL",
    DERIV_SAFETY_MECH: "SAFETY MECH",
    DERIV_CYBERSEC:    "CYBERSEC IMPL",
}

syrs_by_id = {item.id: item for item in syrs_items}
rows = []
for link in links:
    sys_item = syrs_by_id.get(link.source_id)
    sw_item  = next((s for s in swrs_items if s.id == link.target_id), None)
    if sys_item and sw_item:
        rows.append({
            "SyRS ID":    link.source_id,
            "SyRS Title": sys_item.title,
            "ASIL":       sys_item.asil.value,
            "CyberSec":   "Yes" if sys_item.cybersecurity_relevant else "",
            "Derivation": _DERIV_LABEL.get(link.link_type, link.link_type),
            "SwRS ID":    link.target_id,
        })

df = pd.DataFrame(rows)

_ASIL_BG = {
    "ASIL-D": "background-color:#ffcccc",
    "ASIL-C": "background-color:#ffe0cc",
    "ASIL-B": "background-color:#fff3cc",
    "ASIL-A": "background-color:#f0f5cc",
    "QM":     "background-color:#e0f5e0",
}
_DERIV_BG = {
    "FUNCTIONAL":    "background-color:#e8f4fd",
    "SAFETY MECH":   "background-color:#fff3cc",
    "CYBERSEC IMPL": "background-color:#f3e8fd",
}

def highlight_asil(val):
    return _ASIL_BG.get(val, "")

def highlight_deriv(val):
    return _DERIV_BG.get(val, "")

styled = (
    df.style
    .applymap(highlight_asil,  subset=["ASIL"])
    .applymap(highlight_deriv, subset=["Derivation"])
)
st.dataframe(styled, use_container_width=True, hide_index=True)

# ── 5. Draft SwRS items ───────────────────────────────────────────────────────

st.divider()
st.subheader("Draft Software Requirements")
st.caption(
    "AI-assisted draft — all items require human review and approval "
    "before being treated as normative work products (AutoPragma FR-015 / FR-007)."
)

for item in swrs_items:
    badge_html = asil_badge(item.asil)
    if item.cybersecurity_relevant:
        badge_html += " " + cybersec_badge()
    badge_html += " " + derivation_badge(item.derivation_type)

    header = f"{item.id} — {item.title}"
    with st.expander(header, expanded=False):
        st.markdown(f"**ASIL / Classification:** {badge_html}", unsafe_allow_html=True)

        col_l, col_r = st.columns(2)
        col_l.markdown(f"**Type:** `{item.type}`")
        col_r.markdown(f"**Verification:** `{item.verification_method.value}`")
        col_l.markdown(f"**Derived from:** `{item.derived_from}`")
        col_r.markdown(f"**Status:** `{item.status}`")

        st.markdown("**Requirement:**")
        st.info(item.text)

        st.markdown("**Rationale:**")
        st.markdown(item.rationale)

        if item.tags:
            st.markdown("**Tags:** " + " ".join(f"`{t}`" for t in item.tags))

# ── 6. Download outputs ───────────────────────────────────────────────────────

st.divider()
st.subheader("Export")

from swe1.report import write_outputs
json_path, md_path = write_outputs(
    metadata=metadata,
    swrs_items=swrs_items,
    links=links,
    findings=findings,
    output_dir="output/swe1",
)

col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    st.download_button(
        label="Download SwRS JSON",
        data=json_path.read_bytes(),
        file_name="swrs_output.json",
        mime="application/json",
        use_container_width=True,
    )
with col_dl2:
    st.download_button(
        label="Download SWE.1 Report (Markdown)",
        data=md_path.read_bytes(),
        file_name="swe1_report.md",
        mime="text/markdown",
        use_container_width=True,
    )
