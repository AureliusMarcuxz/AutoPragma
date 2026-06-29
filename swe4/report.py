"""
Generate SWE.4 outputs:
  - suvs_output.json  — machine-readable SW Unit Verification Specification
  - swe4_report.md    — human-readable gate evidence document
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from swe3.models import SwUnit

from .models import StaticCheckItem, UnitTestCase, UnitVerificationLink

_CAT_LABEL = {
    "positive":        "POSITIVE",
    "negative":        "NEGATIVE",
    "boundary":        "BOUNDARY",
    "structural":      "STRUCTURAL",
}
_STATIC_LABEL = {
    "MISRA_C":       "MISRA C:2012",
    "complexity":    "Complexity",
    "documentation": "Documentation",
    "naming":        "Naming",
}
_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def write_outputs(
    metadata: dict,
    units: list[SwUnit],
    test_cases: list[UnitTestCase],
    static_checks: list[StaticCheckItem],
    links: list[UnitVerificationLink],
    output_dir: str,
) -> tuple[Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "suvs_output.json"
    md_path   = out / "swe4_report.md"

    _write_json(metadata, test_cases, static_checks, links, json_path)
    _write_markdown(metadata, units, test_cases, static_checks, links, md_path)

    return json_path, md_path


# ── JSON ──────────────────────────────────────────────────────────────────────

def _tc_to_dict(tc: UnitTestCase) -> dict:
    d = asdict(tc)
    d["asil"] = tc.asil.value
    return d


def _sca_to_dict(chk: StaticCheckItem) -> dict:
    d = asdict(chk)
    d["asil"] = chk.asil.value
    return d


def _write_json(
    metadata: dict,
    test_cases: list[UnitTestCase],
    static_checks: list[StaticCheckItem],
    links: list[UnitVerificationLink],
    path: Path,
) -> None:
    cat_counts: dict[str, int] = {}
    for tc in test_cases:
        cat_counts[tc.test_category] = cat_counts.get(tc.test_category, 0) + 1

    payload = {
        "metadata": {
            **metadata,
            "generated_by": "AutoPragma SWE.4 processor",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dynamic_test_count": len(test_cases),
            "static_check_count": len(static_checks),
            "link_count": len(links),
            "category_breakdown": cat_counts,
            "priority_breakdown": {
                p: sum(1 for tc in test_cases if tc.priority == p)
                for p in ("critical", "high", "medium", "low")
            },
        },
        "unit_test_cases": [_tc_to_dict(tc) for tc in test_cases],
        "static_checks":   [_sca_to_dict(chk) for chk in static_checks],
        "links":           [asdict(lnk) for lnk in links],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Markdown ──────────────────────────────────────────────────────────────────

def _write_markdown(
    metadata: dict,
    units: list[SwUnit],
    test_cases: list[UnitTestCase],
    static_checks: list[StaticCheckItem],
    links: list[UnitVerificationLink],
    path: Path,
) -> None:
    project_key = metadata.get("project_key", "PROJ")
    unit_map = {u.id: u for u in units}

    cat_counts: dict[str, int] = {}
    for tc in test_cases:
        cat_counts[tc.test_category] = cat_counts.get(tc.test_category, 0) + 1

    n_critical = sum(1 for tc in test_cases if tc.priority == "critical")
    n_high     = sum(1 for tc in test_cases if tc.priority == "high")
    n_medium   = sum(1 for tc in test_cases if tc.priority == "medium")

    lines: list[str] = []

    # Header
    lines += [
        "# AutoPragma — SWE.4 SW Unit Verification Specification",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Source SwDD | {metadata.get('document_id', '—')} v{metadata.get('version', '—')} |",
        f"| Project | {project_key} |",
        f"| Generated | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} |",
        f"| Dynamic test cases | {len(test_cases)} |",
        f"| Static analysis items | {len(static_checks)} |",
        f"| — Critical | {n_critical} |",
        f"| — High | {n_high} |",
        f"| — Medium | {n_medium} |",
        "",
        "> **Status:** AI-assisted draft. All verification items require human "
        "> review and approval before being treated as normative work products "
        "> (AutoPragma FR-015 / FR-007).",
        "",
    ]

    # Summary by category
    lines += [
        "## 1. Verification Summary",
        "",
        "| Category | Count |",
        "|---|---|",
    ]
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {_CAT_LABEL.get(cat, cat.upper())} | {count} |")
    lines += [
        f"| MISRA C:2012 checks | {sum(1 for c in static_checks if c.category == 'MISRA_C')} |",
        f"| Complexity checks | {sum(1 for c in static_checks if c.category == 'complexity')} |",
        f"| Documentation checks | {sum(1 for c in static_checks if c.category == 'documentation')} |",
        "",
    ]

    # Traceability matrix unit → verification items
    lines += [
        "## 2. Traceability Matrix — SW Unit → Verification Items",
        "",
        "| Unit ID | Unit Name | ASIL | Item ID | Category |",
        "|---|---|---|---|---|",
    ]
    tc_map  = {tc.id: tc for tc in test_cases}
    sca_map = {chk.id: chk for chk in static_checks}
    for lnk in links:
        if lnk.item_type == "dynamic_test":
            tc = tc_map.get(lnk.item_id)
            if tc:
                lines.append(
                    f"| {lnk.unit_id} | {tc.unit_name} | {tc.asil.value} "
                    f"| {lnk.item_id} | {_CAT_LABEL.get(tc.test_category, tc.test_category)} |"
                )
        else:
            chk = sca_map.get(lnk.item_id)
            if chk:
                lines.append(
                    f"| {lnk.unit_id} | {chk.unit_name} | {chk.asil.value} "
                    f"| {lnk.item_id} | {_STATIC_LABEL.get(chk.category, chk.category)} |"
                )
    lines.append("")

    # Dynamic test cases
    lines += [
        "## 3. Dynamic Unit Test Cases (Draft — Pending Review)",
        "",
    ]
    for tc in sorted(test_cases, key=lambda t: _PRIORITY_ORDER.get(t.priority, 9)):
        asil_badge  = f"`{tc.asil.value}`"
        cyber_badge = " `CYBERSEC`" if tc.cybersecurity_relevant else ""
        cat_badge   = f"`{_CAT_LABEL.get(tc.test_category, tc.test_category)}`"

        lines += [
            f"### {tc.id} — {tc.title}",
            "",
            f"**Unit:** `{tc.unit_name}` ({tc.component_name})  ",
            f"**ASIL:** {asil_badge}{cyber_badge}  ",
            f"**Category:** {cat_badge}  ",
            f"**Environment:** `{tc.environment}`  ",
            f"**Priority:** `{tc.priority.upper()}`  ",
            f"**Coverage target:** `{tc.coverage_target}`  ",
            f"**Status:** `{tc.status}`",
            "",
            "**Objective:**",
            f"> {tc.objective}",
            "",
            "**Preconditions:**",
        ]
        for pre in tc.preconditions:
            lines.append(f"- {pre}")
        lines += ["", "**Inputs / Stimuli:**"]
        for inp in tc.inputs:
            lines.append(f"- {inp}")
        lines += ["", "**Expected outputs:**"]
        for exp in tc.expected_outputs:
            lines.append(f"- {exp}")
        lines += [
            "",
            "**Pass criteria:**",
            f"> {tc.pass_criteria}",
            "",
            "**Fail criteria:**",
            f"> {tc.fail_criteria}",
            "",
            "---",
            "",
        ]

    # Static analysis items
    lines += [
        "## 4. Static Analysis Items",
        "",
    ]
    for chk in static_checks:
        lines += [
            f"### {chk.id} — {_STATIC_LABEL.get(chk.category, chk.category)} — {chk.unit_name}",
            "",
            f"**Unit:** `{chk.unit_name}` ({chk.component_name})  ",
            f"**ASIL:** `{chk.asil.value}`  ",
            f"**Tool:** {chk.tool}  ",
            f"**Status:** `{chk.status}`",
            "",
            f"**Description:** {chk.description}",
            "",
            f"**Acceptance criteria:** {chk.acceptance_criteria}",
            "",
            "---",
            "",
        ]

    path.write_text("\n".join(lines), encoding="utf-8")
