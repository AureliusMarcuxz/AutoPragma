"""
Generate SWE.5 outputs:
  - sits_output.json  — SW Integration Test Specification (machine-readable)
  - swe5_report.md    — human-readable gate evidence document
  - integration_sequence.puml — PlantUML sequence diagram
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from swe2.models import SwComponent
from swe3.models import SwUnit

from .models import IntegrationLink, IntegrationStage, IntegrationTestCase
from .render import render_integration_sequence

_TYPE_LABEL = {
    "interface_contract":    "INTERFACE CONTRACT",
    "data_flow":             "DATA FLOW",
    "timing_interaction":    "TIMING INTERACTION",
    "error_propagation":     "ERROR PROPAGATION",
    "safety_chain":          "SAFETY CHAIN",
    "security_chain":        "SECURITY CHAIN",
}
_LEVEL_LABEL = {
    "intra_component":  "INTRA-COMPONENT",
    "cross_component":  "CROSS-COMPONENT",
    "full":             "FULL",
}
_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def write_outputs(
    metadata: dict,
    components: list[SwComponent],
    units: list[SwUnit],
    itcs: list[IntegrationTestCase],
    links: list[IntegrationLink],
    stages: list[IntegrationStage],
    output_dir: str,
) -> tuple[Path, Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "sits_output.json"
    md_path   = out / "swe5_report.md"
    puml_path = out / "integration_sequence.puml"

    _write_json(metadata, itcs, links, stages, json_path)
    _write_markdown(metadata, components, units, itcs, links, stages, md_path)

    project_key = metadata.get("project_key", "PROJ")
    puml = render_integration_sequence(components, units, stages, project_key, metadata)
    puml_path.write_text(puml, encoding="utf-8")

    return json_path, md_path, puml_path


# ── JSON ──────────────────────────────────────────────────────────────────────

def _itc_to_dict(itc: IntegrationTestCase) -> dict:
    d = asdict(itc)
    d["asil"] = itc.asil.value
    return d


def _stage_to_dict(stage: IntegrationStage) -> dict:
    return {
        "stage_number":       stage.stage_number,
        "title":              stage.title,
        "description":        stage.description,
        "integration_level":  stage.integration_level,
        "components_covered": stage.components_covered,
        "steps": [
            {
                "step_number":  s.step_number,
                "title":        s.title,
                "units":        s.units,
                "components":   s.components,
                "stubs_needed": s.stubs_needed,
                "exit_criteria": s.exit_criteria,
            }
            for s in stage.steps
        ],
    }


def _write_json(
    metadata: dict,
    itcs: list[IntegrationTestCase],
    links: list[IntegrationLink],
    stages: list[IntegrationStage],
    path: Path,
) -> None:
    type_counts: dict[str, int] = {}
    for itc in itcs:
        type_counts[itc.test_type] = type_counts.get(itc.test_type, 0) + 1

    payload = {
        "metadata": {
            **metadata,
            "generated_by": "AutoPragma SWE.5 processor",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "itc_count":         len(itcs),
            "link_count":        len(links),
            "stage_count":       len(stages),
            "intra_component_count": sum(
                1 for i in itcs if i.integration_level == "intra_component"
            ),
            "cross_component_count": sum(
                1 for i in itcs if i.integration_level == "cross_component"
            ),
            "type_breakdown":    type_counts,
            "priority_breakdown": {
                p: sum(1 for i in itcs if i.priority == p)
                for p in ("critical", "high", "medium")
            },
        },
        "integration_stages": [_stage_to_dict(s) for s in stages],
        "integration_test_cases": [_itc_to_dict(i) for i in itcs],
        "links": [asdict(lnk) for lnk in links],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Markdown ──────────────────────────────────────────────────────────────────

def _write_markdown(
    metadata: dict,
    components: list[SwComponent],
    units: list[SwUnit],
    itcs: list[IntegrationTestCase],
    links: list[IntegrationLink],
    stages: list[IntegrationStage],
    path: Path,
) -> None:
    project_key  = metadata.get("project_key", "PROJ")
    n_intra      = sum(1 for i in itcs if i.integration_level == "intra_component")
    n_cross      = sum(1 for i in itcs if i.integration_level == "cross_component")
    n_critical   = sum(1 for i in itcs if i.priority == "critical")
    n_high       = sum(1 for i in itcs if i.priority == "high")

    lines: list[str] = []

    # Header
    lines += [
        "# AutoPragma — SWE.5 Software Integration Test Specification",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Source SwDD | {metadata.get('document_id', '—')} v{metadata.get('version', '—')} |",
        f"| Project | {project_key} |",
        f"| Generated | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} |",
        f"| Total ITC count | {len(itcs)} |",
        f"| — Intra-component | {n_intra} |",
        f"| — Cross-component | {n_cross} |",
        f"| — Critical | {n_critical} |",
        f"| — High | {n_high} |",
        f"| Integration stages | {len(stages)} |",
        "",
        "> **Status:** AI-assisted draft. All integration test cases require human "
        "> review and approval before being treated as normative work products "
        "> (AutoPragma FR-015 / FR-007).",
        "",
    ]

    # Type breakdown
    type_counts: dict[str, int] = {}
    for itc in itcs:
        type_counts[itc.test_type] = type_counts.get(itc.test_type, 0) + 1

    lines += [
        "## 1. ITC Type Breakdown",
        "",
        "| Test Type | Count |",
        "|---|---|",
    ]
    for ttype, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {_TYPE_LABEL.get(ttype, ttype.upper())} | {cnt} |")
    lines.append("")

    # Integration plan
    lines += [
        "## 2. Integration Plan",
        "",
    ]
    for stage in stages:
        lines += [
            f"### Stage {stage.stage_number} — {stage.title}",
            "",
            f"**Level:** `{_LEVEL_LABEL.get(stage.integration_level, stage.integration_level)}`",
            "",
            f"{stage.description}",
            "",
            "| Step | Title | Units | Exit Criteria |",
            "|---|---|---|---|",
        ]
        for step in stage.steps:
            units_str = ", ".join(step.units[:2]) + ("…" if len(step.units) > 2 else "")
            lines.append(
                f"| {step.step_number} | {step.title} | {units_str} | {step.exit_criteria[:80]}… |"
                if len(step.exit_criteria) > 80
                else f"| {step.step_number} | {step.title} | {units_str} | {step.exit_criteria} |"
            )
        lines.append("")

    # Traceability matrix
    lines += [
        "## 3. Traceability Matrix — Component Pairs → Integration Test Cases",
        "",
        "| ITC ID | Test Type | Level | ASIL | Components | Priority |",
        "|---|---|---|---|---|---|",
    ]
    for itc in sorted(itcs, key=lambda i: _PRIORITY_ORDER.get(i.priority, 9)):
        comp_str = ", ".join(itc.components_covered[:2])
        lines.append(
            f"| {itc.id} | {_TYPE_LABEL.get(itc.test_type, itc.test_type)} "
            f"| {_LEVEL_LABEL.get(itc.integration_level, itc.integration_level)} "
            f"| {itc.asil.value} | {comp_str} | {itc.priority.upper()} |"
        )
    lines.append("")

    # ITC cards
    lines += [
        "## 4. Integration Test Cases (Draft — Pending Review)",
        "",
    ]
    for itc in sorted(itcs, key=lambda i: _PRIORITY_ORDER.get(i.priority, 9)):
        type_label  = _TYPE_LABEL.get(itc.test_type, itc.test_type.upper())
        level_label = _LEVEL_LABEL.get(itc.integration_level, itc.integration_level)
        cyber_str   = "  `CYBERSEC`" if itc.cybersecurity_relevant else ""

        lines += [
            f"### {itc.id} — {itc.title}",
            "",
            f"**ASIL:** `{itc.asil.value}`{cyber_str}  ",
            f"**Type:** `{type_label}`  ",
            f"**Level:** `{level_label}`  ",
            f"**Environment:** `{itc.environment}`  ",
            f"**Priority:** `{itc.priority.upper()}`  ",
            f"**Status:** `{itc.status}`",
            "",
            f"**Units under test:** {', '.join(f'`{u}`' for u in itc.units_under_test)}",
            "",
            "**Objective:**",
            f"> {itc.objective}",
            "",
            "**Preconditions:**",
        ]
        for pre in itc.preconditions:
            lines.append(f"- {pre}")
        lines += ["", "**Stimuli:**"]
        for stim in itc.stimuli:
            lines.append(f"- {stim}")
        lines += ["", "**Expected behaviour:**"]
        for exp in itc.expected_behavior:
            lines.append(f"- {exp}")
        lines += [
            "",
            "**Pass criteria:**",
            f"> {itc.pass_criteria}",
            "",
            "**Fail criteria:**",
            f"> {itc.fail_criteria}",
            "",
            "**Coverage tags:** " + " ".join(f"`{t}`" for t in itc.coverage_tags),
            "",
            "---",
            "",
        ]

    path.write_text("\n".join(lines), encoding="utf-8")
