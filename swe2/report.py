"""
Generate SWE.2 outputs:
  - swad_output.json          — machine-readable architectural design + allocation
  - swe2_report.md            — human-readable gate evidence with PlantUML inline
  - component_diagram.puml    — full component diagram source
  - safety_diagram.puml       — safety architecture diagram source
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from swe1.models import SwRSItem
from .models import AllocationLink, SwComponent
from .render import render_component_diagram, render_safety_diagram


def write_outputs(
    metadata: dict,
    components: list[SwComponent],
    links: list[AllocationLink],
    swrs_items: list[SwRSItem],
    output_dir: str,
) -> tuple[Path, Path, Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    project_key = metadata.get("project_key", "PROJ")

    comp_puml_src  = render_component_diagram(components, project_key, metadata)
    safety_puml_src = render_safety_diagram(components, project_key, metadata)

    json_path        = out / "swad_output.json"
    md_path          = out / "swe2_report.md"
    comp_puml_path   = out / "component_diagram.puml"
    safety_puml_path = out / "safety_diagram.puml"

    comp_puml_path.write_text(comp_puml_src, encoding="utf-8")
    safety_puml_path.write_text(safety_puml_src, encoding="utf-8")

    _write_json(metadata, components, links, json_path)
    _write_markdown(metadata, components, links, swrs_items,
                    comp_puml_src, safety_puml_src, md_path)

    return json_path, md_path, comp_puml_path, safety_puml_path


# ── JSON ──────────────────────────────────────────────────────────────────────

def _comp_to_dict(c: SwComponent) -> dict:
    d = asdict(c)
    d["asil"] = c.asil.value
    return d


def _write_json(
    metadata: dict,
    components: list[SwComponent],
    links: list[AllocationLink],
    path: Path,
) -> None:
    layer_counts: dict[str, int] = {}
    for c in components:
        layer_counts[c.layer] = layer_counts.get(c.layer, 0) + 1

    payload = {
        "metadata": {
            **metadata,
            "generated_by": "AutoPragma SWE.2 processor",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "component_count": len(components),
            "allocation_links": len(links),
            "layer_breakdown": layer_counts,
        },
        "components": [_comp_to_dict(c) for c in components],
        "allocation": [asdict(lnk) for lnk in links],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Markdown ──────────────────────────────────────────────────────────────────

def _write_markdown(
    metadata: dict,
    components: list[SwComponent],
    links: list[AllocationLink],
    swrs_items: list[SwRSItem],
    comp_puml: str,
    safety_puml: str,
    path: Path,
) -> None:
    project_key = metadata.get("project_key", "PROJ")
    swrs_by_id = {item.id: item for item in swrs_items}

    layer_counts: dict[str, int] = {}
    for c in components:
        layer_counts[c.layer] = layer_counts.get(c.layer, 0) + 1

    lines: list[str] = []

    # Header
    lines += [
        "# AutoPragma — SWE.2 Architectural Design Report",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Source SwRS | {metadata.get('document_id', '—')} v{metadata.get('version', '—')} |",
        f"| Project | {project_key} |",
        f"| Generated | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} |",
        f"| SW Components | {len(components)} "
        f"(app: {layer_counts.get('application', 0)}, "
        f"safety: {layer_counts.get('safety', 0)}, "
        f"security: {layer_counts.get('security', 0)}) |",
        f"| Allocation links | {len(links)} |",
        "",
        "> **Status:** AI-assisted draft. All architectural decisions require human "
        "> review and approval before being treated as normative work products "
        "> (AutoPragma FR-007 / FR-015).",
        "",
    ]

    # Component catalogue
    lines += [
        "## 1. Software Component Catalogue",
        "",
    ]
    for comp in components:
        asil_badge = f"`{comp.asil.value}`"
        cyber_badge = " `CYBERSEC`" if comp.cybersecurity_relevant else ""
        layer_badge = f"`{comp.layer.upper()}`"
        lines += [
            f"### {comp.id} — {comp.name}",
            "",
            f"**Layer:** {layer_badge}  ",
            f"**ASIL:** {asil_badge}{cyber_badge}  ",
            f"**Allocated SwRS:** {len(comp.allocated_swrs)} items  ",
            "",
            f"{comp.description}",
            "",
        ]
        if comp.monitors:
            lines.append(f"**Monitors:** {', '.join(f'`{m}`' for m in comp.monitors)}  ")
        if comp.secures:
            lines.append(f"**Secures:** {', '.join(f'`{s}`' for s in comp.secures)}  ")
        if comp.monitors or comp.secures:
            lines.append("")
        lines += ["---", ""]

    # Allocation matrix
    lines += [
        "## 2. Requirement Allocation Matrix (SwRS → Component)",
        "",
        "| SwRS ID | Derivation | Component | Layer | ASIL |",
        "|---|---|---|---|---|",
    ]
    deriv_label = {
        "derives_functional":       "FUNCTIONAL",
        "derives_safety_mechanism": "SAFETY MECH",
        "derives_cybersec_impl":    "CYBERSEC IMPL",
    }
    for lnk in links:
        item = swrs_by_id.get(lnk.swrs_id)
        comp = next((c for c in components if c.id == lnk.component_id), None)
        if item and comp:
            dlabel = deriv_label.get(item.derivation_type, item.derivation_type)
            lines.append(
                f"| {lnk.swrs_id} | {dlabel} | {comp.name} | {comp.layer} | {comp.asil.value} |"
            )
    lines.append("")

    # PlantUML diagrams
    lines += [
        "## 3. Component Diagram (PlantUML source)",
        "",
        "Render with: PlantUML CLI · VS Code PlantUML extension · IntelliJ PlantUML plugin",
        "",
        "```plantuml",
        comp_puml,
        "```",
        "",
        "## 4. Safety Architecture Diagram (PlantUML source)",
        "",
        "```plantuml",
        safety_puml,
        "```",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
