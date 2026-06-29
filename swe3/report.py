"""
Generate SWE.3 outputs:
  - swdd_output.json    — machine-readable SW Detailed Design
  - swe3_report.md      — human-readable gate evidence document
  - detailed_design.puml — PlantUML class diagram source
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from swe2.models import SwComponent

from .models import SwUnit, UnitLink
from .render import render_detailed_design

_LAYER_LABEL = {
    "application": "APPLICATION",
    "safety":      "SAFETY",
    "security":    "SECURITY",
}


def write_outputs(
    metadata: dict,
    components: list[SwComponent],
    units: list[SwUnit],
    links: list[UnitLink],
    output_dir: str,
) -> tuple[Path, Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    project_key = metadata.get("project_key", "PROJ")
    puml_src = render_detailed_design(components, units, links, project_key, metadata)

    json_path = out / "swdd_output.json"
    md_path   = out / "swe3_report.md"
    puml_path = out / "detailed_design.puml"

    puml_path.write_text(puml_src, encoding="utf-8")
    _write_json(metadata, units, links, json_path)
    _write_markdown(metadata, components, units, links, puml_src, md_path)

    return json_path, md_path, puml_path


# ── JSON ──────────────────────────────────────────────────────────────────────

def _unit_to_dict(u: SwUnit) -> dict:
    d = asdict(u)
    d["asil"] = u.asil.value
    return d


def _write_json(
    metadata: dict,
    units: list[SwUnit],
    links: list[UnitLink],
    path: Path,
) -> None:
    layer_counts: dict[str, int] = {}
    for u in units:
        layer_counts[u.layer] = layer_counts.get(u.layer, 0) + 1

    payload = {
        "metadata": {
            **metadata,
            "generated_by": "AutoPragma SWE.3 processor",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "unit_count": len(units),
            "link_count": len(links),
            "layer_breakdown": layer_counts,
        },
        "units": [_unit_to_dict(u) for u in units],
        "links": [asdict(lnk) for lnk in links],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Markdown ──────────────────────────────────────────────────────────────────

def _write_markdown(
    metadata: dict,
    components: list[SwComponent],
    units: list[SwUnit],
    links: list[UnitLink],
    puml_src: str,
    path: Path,
) -> None:
    project_key = metadata.get("project_key", "PROJ")

    layer_counts: dict[str, int] = {}
    for u in units:
        layer_counts[u.layer] = layer_counts.get(u.layer, 0) + 1

    units_by_comp: dict[str, list[SwUnit]] = {}
    for u in units:
        units_by_comp.setdefault(u.component_id, []).append(u)

    dep_links = [lnk for lnk in links if lnk.link_type == "depends"]
    unit_id_to_name = {u.id: u.name for u in units}

    lines: list[str] = []

    # Header
    lines += [
        "# AutoPragma — SWE.3 Software Detailed Design",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Source SwAD | {metadata.get('document_id', '—')} v{metadata.get('version', '—')} |",
        f"| Project | {project_key} |",
        f"| Generated | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} |",
        f"| SW Units | {len(units)} "
        f"(app: {layer_counts.get('application', 0)}, "
        f"safety: {layer_counts.get('safety', 0)}, "
        f"security: {layer_counts.get('security', 0)}) |",
        f"| Unit links | {len(links)} |",
        "",
        "> **Status:** AI-assisted draft. All design decisions require human review "
        "> and approval before being treated as normative work products "
        "> (AutoPragma FR-007 / FR-015).",
        "",
    ]

    # Component decomposition summary
    lines += [
        "## 1. Component → Unit Decomposition",
        "",
        "| Component | Layer | ASIL | Unit | Responsibility (summary) |",
        "|---|---|---|---|---|",
    ]
    for comp in components:
        for u in units_by_comp.get(comp.id, []):
            resp_short = u.responsibility[:80].rstrip() + "…"
            lines.append(
                f"| {comp.name} | {_LAYER_LABEL.get(comp.layer, comp.layer)} "
                f"| {comp.asil.value} | {u.name} | {resp_short} |"
            )
    lines.append("")

    # Unit dependency summary
    if dep_links:
        lines += [
            "## 2. Unit Dependencies",
            "",
            "| From Unit | To Unit | Link |",
            "|---|---|---|",
        ]
        for lnk in dep_links:
            src = unit_id_to_name.get(lnk.component_id, lnk.component_id)
            tgt = unit_id_to_name.get(lnk.unit_id, lnk.unit_id)
            lines.append(f"| {src} | {tgt} | calls / uses |")
        lines.append("")

    # Detailed unit specifications
    lines += [
        "## 3. SW Unit Specifications (Draft — Pending Review)",
        "",
    ]

    section = 1
    for comp in components:
        comp_units = units_by_comp.get(comp.id, [])
        if not comp_units:
            continue
        cyber_tag = " | CYBERSEC" if comp.cybersecurity_relevant else ""
        lines += [
            f"### 3.{section} {comp.name} [{comp.asil.value}{cyber_tag}] — "
            f"{_LAYER_LABEL.get(comp.layer, comp.layer)} Layer",
            "",
        ]
        section += 1

        for u in comp_units:
            asil_badge  = f"`{u.asil.value}`"
            cyber_badge = " `CYBERSEC`" if u.cybersecurity_relevant else ""
            lines += [
                f"#### {u.id} — {u.name}",
                "",
                f"**ASIL:** {asil_badge}{cyber_badge}  ",
                f"**Layer:** `{_LAYER_LABEL.get(u.layer, u.layer)}`  ",
                f"**Parent component:** `{u.component_name}`  ",
                f"**Status:** `{u.status}`",
                "",
                "**Responsibility:**",
                f"> {u.responsibility}",
                "",
                "**Provided interface:**",
                "",
                "| Operation | Parameters | Returns | Description |",
                "|---|---|---|---|",
            ]
            for op in u.interface.provided:
                params = ", ".join(op.parameters) if op.parameters else "—"
                lines.append(f"| `{op.name}` | {params} | `{op.return_type}` | {op.description} |")
            lines.append("")

            if u.interface.required:
                lines += [
                    "**Required services:**",
                    "",
                ]
                for req in u.interface.required:
                    lines.append(f"- {req}")
                lines.append("")

            if u.internal_data:
                lines += [
                    "**Internal data elements:**",
                    "",
                ]
                for datum in u.internal_data:
                    lines.append(f"- `{datum}`")
                lines.append("")

            if u.allocated_swrs:
                lines += [
                    f"**Allocated SwRS items:** "
                    + ", ".join(f"`{s}`" for s in u.allocated_swrs),
                    "",
                ]

            lines += ["---", ""]

    # PlantUML diagram
    lines += [
        "## 4. Detailed Design Diagram (PlantUML source)",
        "",
        "Render with: PlantUML CLI · VS Code PlantUML extension · plantuml.com",
        "",
        "```plantuml",
        puml_src,
        "```",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
