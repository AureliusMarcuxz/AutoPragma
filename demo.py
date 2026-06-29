"""
AutoPragma — Interactive Demo
Run: py -m streamlit run demo.py
"""

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from swe1 import derive_swrs, load_syrs, validate
from swe1.derive import DERIV_CYBERSEC, DERIV_FUNCTIONAL, DERIV_SAFETY_MECH
from swe1.models import ASIL
from swe1.report import write_outputs as swe1_write_outputs
from swe1.validate import finding_counts
from swe2 import allocate_swad
from swe2.report import write_outputs as swe2_write_outputs

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AutoPragma",
    page_icon="images/autopragma-logo.png" if Path("images/autopragma-logo.png").exists() else ":gear:",
    layout="wide",
)

SAMPLE_PATH = Path(__file__).parent / "sample_data" / "sys_requirements.json"

# ── Badge helpers ─────────────────────────────────────────────────────────────

_ASIL_BADGE_COLOR = {
    ASIL.D:  ("#7f0000", "#ffcccc"),
    ASIL.C:  ("#7f2000", "#ffe0cc"),
    ASIL.B:  ("#7f5000", "#fff3cc"),
    ASIL.A:  ("#4a5a00", "#f0f5cc"),
    ASIL.QM: ("#1a5a1a", "#e0f5e0"),
}

def asil_badge(asil: ASIL) -> str:
    fg, bg = _ASIL_BADGE_COLOR.get(asil, ("#333", "#eee"))
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:4px;font-weight:700;font-size:0.85em;">{asil.value}</span>'
    )

def cybersec_badge() -> str:
    return (
        '<span style="background:#dde8ff;color:#003080;padding:2px 8px;'
        'border-radius:4px;font-weight:700;font-size:0.85em;">CYBERSEC</span>'
    )

_DERIV_BADGE_STYLE = {
    DERIV_FUNCTIONAL:  ("FUNCTIONAL",    "#e8f4fd", "#0a4a7a"),
    DERIV_SAFETY_MECH: ("SAFETY MECH",   "#fff3cc", "#7f5000"),
    DERIV_CYBERSEC:    ("CYBERSEC IMPL", "#f3e8fd", "#5a0a7a"),
}

def derivation_badge(deriv_type: str) -> str:
    label, bg, fg = _DERIV_BADGE_STYLE.get(deriv_type, (deriv_type, "#eee", "#333"))
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:4px;font-weight:700;font-size:0.85em;">{label}</span>'
    )

def layer_badge(layer: str) -> str:
    colors = {
        "application": ("#0a4a7a", "#e8f4fd"),
        "safety":      ("#7f5000", "#fff3cc"),
        "security":    ("#5a0a7a", "#f3e8fd"),
    }
    fg, bg = colors.get(layer, ("#333", "#eee"))
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:4px;font-weight:700;font-size:0.85em;">{layer.upper()}</span>'
    )

# ── DataFrame cell stylers ────────────────────────────────────────────────────

_ASIL_CELL = {
    "ASIL-D": "background-color:#ffcccc; color:#7f0000",
    "ASIL-C": "background-color:#ffe0cc; color:#7f2000",
    "ASIL-B": "background-color:#fff3cc; color:#7f5000",
    "ASIL-A": "background-color:#f0f5cc; color:#4a5a00",
    "QM":     "background-color:#e0f5e0; color:#1a5a1a",
}
_DERIV_CELL = {
    "FUNCTIONAL":    "background-color:#e8f4fd; color:#0a4a7a",
    "SAFETY MECH":   "background-color:#fff3cc; color:#7f5000",
    "CYBERSEC IMPL": "background-color:#f3e8fd; color:#5a0a7a",
}
_LAYER_CELL = {
    "application": "background-color:#e8f4fd; color:#0a4a7a",
    "safety":      "background-color:#fff3cc; color:#7f5000",
    "security":    "background-color:#f3e8fd; color:#5a0a7a",
}

_DERIV_LABEL = {
    DERIV_FUNCTIONAL:  "FUNCTIONAL",
    DERIV_SAFETY_MECH: "SAFETY MECH",
    DERIV_CYBERSEC:    "CYBERSEC IMPL",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("AutoPragma")
    st.caption("ASPICE Process Automation Platform")
    st.divider()

    st.subheader("SWE.1 + SWE.2 Pipeline")
    st.markdown(
        "Upload a System Requirements Specification (SyRS) JSON file "
        "exported from your ALM tool, or use the built-in sample."
    )

    input_mode = st.radio("Input source", ["Sample SyRS (VSC)", "Upload file"])

    uploaded = None
    if input_mode == "Upload file":
        uploaded = st.file_uploader("SyRS JSON file", type=["json"])

    st.divider()
    run = st.button("Run SWE.1 + SWE.2 Analysis", type="primary", use_container_width=True)

    st.divider()
    st.caption("ASPICE CL3 | ISO 26262 | ISO/SAE 21434 | MISRA")

# ── Main header ───────────────────────────────────────────────────────────────

st.markdown("## AutoPragma — ASPICE SWE.1 + SWE.2 Pipeline")
st.markdown(
    "Ingests a system-level requirements specification (SyRS), derives and validates "
    "a draft software requirements specification (SWE.1), then generates the software "
    "architectural design expressed as PlantUML component diagrams (SWE.2)."
)

if not run:
    st.info("Configure your input in the sidebar and click **Run SWE.1 + SWE.2 Analysis**.")
    st.stop()

# ── Load SyRS ─────────────────────────────────────────────────────────────────

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

project_key = metadata.get("project_key", "PROJ")

# ── SWE.1 processing ──────────────────────────────────────────────────────────

findings          = validate(syrs_items)
swrs_items, links = derive_swrs(syrs_items, project_key)
counts            = finding_counts(findings)
gate_pass         = counts["ERROR"] == 0

n_functional  = sum(1 for sw in swrs_items if sw.derivation_type == DERIV_FUNCTIONAL)
n_safety_mech = sum(1 for sw in swrs_items if sw.derivation_type == DERIV_SAFETY_MECH)
n_cybersec    = sum(1 for sw in swrs_items if sw.derivation_type == DERIV_CYBERSEC)

# ── SWE.2 processing ──────────────────────────────────────────────────────────

components, comp_links = allocate_swad(swrs_items, project_key)

n_app_comp = sum(1 for c in components if c.layer == "application")
n_saf_comp = sum(1 for c in components if c.layer == "safety")
n_sec_comp = sum(1 for c in components if c.layer == "security")

# ── Metadata banner (shared) ──────────────────────────────────────────────────

st.divider()
b1, b2, b3, b4, b5, b6 = st.columns(6)
b1.metric("Document",       metadata.get("document_id", "—"))
b2.metric("Version",        metadata.get("version", "—"))
b3.metric("Status",         metadata.get("status", "—").upper())
b4.metric("SyRS Items",     len(syrs_items))
b5.metric("SwRS Generated", len(swrs_items))
b6.metric("SW Components",  len(components))

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2 = st.tabs(["SWE.1 — Software Requirements", "SWE.2 — Architectural Design"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SWE.1
# ═══════════════════════════════════════════════════════════════════════════════

with tab1:

    # Derivation breakdown
    d1, d2, d3 = st.columns(3)
    d1.metric("Functional",       n_functional)
    d2.metric("Safety Mechanism", n_safety_mech)
    d3.metric("Cybersec Impl",    n_cybersec)

    # Gate result
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

    # Validation results
    st.divider()
    st.subheader("Validation Results")
    vcol1, vcol2, vcol3 = st.columns(3)
    vcol1.metric("Errors",   counts["ERROR"])
    vcol2.metric("Warnings", counts["WARNING"])
    vcol3.metric("Info",     counts.get("INFO", 0))

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

    # Traceability matrix SyRS → SwRS
    st.divider()
    st.subheader("Traceability Matrix — SyRS → SwRS")

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

    df1 = pd.DataFrame(rows)
    styled1 = (
        df1.style
        .applymap(lambda v: _ASIL_CELL.get(v, ""),  subset=["ASIL"])
        .applymap(lambda v: _DERIV_CELL.get(v, ""), subset=["Derivation"])
    )
    st.dataframe(styled1, use_container_width=True, hide_index=True)

    # Draft SwRS items
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

        with st.expander(f"{item.id} — {item.title}", expanded=False):
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

    # Export SWE.1
    st.divider()
    st.subheader("Export — SWE.1")
    json1, md1 = swe1_write_outputs(
        metadata=metadata, swrs_items=swrs_items, links=links,
        findings=findings, output_dir="output/swe1",
    )
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button("Download SwRS JSON", data=json1.read_bytes(),
                           file_name="swrs_output.json", mime="application/json",
                           use_container_width=True)
    with dl2:
        st.download_button("Download SWE.1 Report (MD)", data=md1.read_bytes(),
                           file_name="swe1_report.md", mime="text/markdown",
                           use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SWE.2
# ═══════════════════════════════════════════════════════════════════════════════

with tab2:

    # Component layer breakdown
    e1, e2, e3 = st.columns(3)
    e1.metric("Application components", n_app_comp)
    e2.metric("Safety components",      n_saf_comp)
    e3.metric("Security components",    n_sec_comp)

    # Component catalogue
    st.divider()
    st.subheader("SW Component Catalogue")

    for comp in components:
        badge_html = asil_badge(comp.asil)
        if comp.cybersecurity_relevant:
            badge_html += " " + cybersec_badge()
        badge_html += " " + layer_badge(comp.layer)

        with st.expander(f"{comp.id} — {comp.name}  ({comp.asil.value} | {comp.layer.upper()})",
                         expanded=True):
            st.markdown(f"**Classification:** {badge_html}", unsafe_allow_html=True)
            st.markdown(f"**Allocated SwRS items:** `{len(comp.allocated_swrs)}`")
            st.markdown(f"**Description:** {comp.description}")

            if comp.monitors:
                st.markdown("**Monitors:** " + " ".join(f"`{m}`" for m in comp.monitors))
            if comp.secures:
                st.markdown("**Secures:** " + " ".join(f"`{s}`" for s in comp.secures))

            if comp.allocated_swrs:
                with st.expander("Allocated SwRS IDs", expanded=False):
                    swrs_by_id_map = {sw.id: sw for sw in swrs_items}
                    for swrs_id in comp.allocated_swrs:
                        sw = swrs_by_id_map.get(swrs_id)
                        if sw:
                            dlabel = _DERIV_LABEL.get(sw.derivation_type, sw.derivation_type)
                            st.markdown(f"- `{swrs_id}` — **{dlabel}** — {sw.title}")

    # Allocation matrix SwRS → Component
    st.divider()
    st.subheader("Allocation Matrix — SwRS → Component")

    swrs_map = {sw.id: sw for sw in swrs_items}
    comp_map = {c.id: c for c in components}

    alloc_rows = []
    for lnk in comp_links:
        sw   = swrs_map.get(lnk.swrs_id)
        comp = comp_map.get(lnk.component_id)
        if sw and comp:
            alloc_rows.append({
                "SwRS ID":    lnk.swrs_id,
                "Derivation": _DERIV_LABEL.get(sw.derivation_type, sw.derivation_type),
                "Component":  comp.name,
                "Layer":      comp.layer,
                "ASIL":       comp.asil.value,
            })

    df2 = pd.DataFrame(alloc_rows)
    styled2 = (
        df2.style
        .applymap(lambda v: _DERIV_CELL.get(v, ""), subset=["Derivation"])
        .applymap(lambda v: _LAYER_CELL.get(v, ""), subset=["Layer"])
        .applymap(lambda v: _ASIL_CELL.get(v, ""),  subset=["ASIL"])
    )
    st.dataframe(styled2, use_container_width=True, hide_index=True)

    # PlantUML diagrams
    st.divider()
    st.subheader("PlantUML Diagrams (Everything as Code)")
    st.caption(
        "Render with: PlantUML CLI · VS Code PlantUML extension · IntelliJ PlantUML plugin · plantuml.com"
    )

    from swe2.render import render_component_diagram, render_safety_diagram
    comp_puml   = render_component_diagram(components, project_key, metadata)
    safety_puml = render_safety_diagram(components, project_key, metadata)

    puml_tab1, puml_tab2 = st.tabs(["Component Diagram", "Safety Architecture Diagram"])

    with puml_tab1:
        st.code(comp_puml, language="text")

    with puml_tab2:
        st.code(safety_puml, language="text")

    # Export SWE.2
    st.divider()
    st.subheader("Export — SWE.2")
    json2, md2, puml_comp, puml_safety = swe2_write_outputs(
        metadata=metadata, components=components, links=comp_links,
        swrs_items=swrs_items, output_dir="output/swe2",
    )
    dl1, dl2, dl3, dl4 = st.columns(4)
    with dl1:
        st.download_button("Download SwAD JSON", data=json2.read_bytes(),
                           file_name="swad_output.json", mime="application/json",
                           use_container_width=True)
    with dl2:
        st.download_button("Download SWE.2 Report (MD)", data=md2.read_bytes(),
                           file_name="swe2_report.md", mime="text/markdown",
                           use_container_width=True)
    with dl3:
        st.download_button("Download component_diagram.puml",
                           data=puml_comp.read_bytes(),
                           file_name="component_diagram.puml", mime="text/plain",
                           use_container_width=True)
    with dl4:
        st.download_button("Download safety_diagram.puml",
                           data=puml_safety.read_bytes(),
                           file_name="safety_diagram.puml", mime="text/plain",
                           use_container_width=True)
