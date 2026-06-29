"""
Generate SWE.6 outputs:
  - sqts_output.json   — machine-readable SW Qualification Test Specification
  - swe6_report.md     — human-readable SQTS gate evidence document
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from swe1.models import SwRSItem

from .models import TestCase, TestCoverageLink

_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_TYPE_LABEL = {
    "behavioral":      "BEHAVIORAL",
    "fault_injection": "FAULT INJECTION",
    "security":        "SECURITY",
    "inspection":      "INSPECTION",
    "static_analysis": "STATIC ANALYSIS",
    "demonstration":   "DEMONSTRATION",
}
_METHOD_LABEL = {
    "dynamic_test":    "Dynamic Test",
    "static_analysis": "Static Analysis",
    "inspection":      "Inspection",
    "demonstration":   "Demonstration",
}


def write_outputs(
    metadata: dict,
    test_cases: list[TestCase],
    links: list[TestCoverageLink],
    swrs_items: list[SwRSItem],
    output_dir: str,
) -> tuple[Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "sqts_output.json"
    md_path   = out / "swe6_report.md"

    _write_json(metadata, test_cases, links, json_path)
    _write_markdown(metadata, test_cases, links, swrs_items, md_path)

    return json_path, md_path


# ── JSON ──────────────────────────────────────────────────────────────────────

def _tc_to_dict(tc: TestCase) -> dict:
    d = asdict(tc)
    d["asil"] = tc.asil.value
    return d


def _write_json(
    metadata: dict,
    test_cases: list[TestCase],
    links: list[TestCoverageLink],
    path: Path,
) -> None:
    type_counts: dict[str, int] = {}
    env_counts: dict[str, int] = {}
    for tc in test_cases:
        type_counts[tc.test_type]   = type_counts.get(tc.test_type, 0) + 1
        env_counts[tc.environment]  = env_counts.get(tc.environment, 0) + 1

    payload = {
        "metadata": {
            **metadata,
            "generated_by": "AutoPragma SWE.6 processor",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "test_case_count": len(test_cases),
            "coverage_links": len(links),
            "type_breakdown": type_counts,
            "environment_breakdown": env_counts,
            "priority_breakdown": {
                p: sum(1 for tc in test_cases if tc.priority == p)
                for p in ("critical", "high", "medium", "low")
            },
        },
        "test_cases": [_tc_to_dict(tc) for tc in test_cases],
        "coverage": [asdict(lnk) for lnk in links],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Markdown ──────────────────────────────────────────────────────────────────

def _write_markdown(
    metadata: dict,
    test_cases: list[TestCase],
    links: list[TestCoverageLink],
    swrs_items: list[SwRSItem],
    path: Path,
) -> None:
    project_key = metadata.get("project_key", "PROJ")
    swrs_by_id  = {sw.id: sw for sw in swrs_items}

    type_counts: dict[str, int] = {}
    env_counts: dict[str, int] = {}
    for tc in test_cases:
        type_counts[tc.test_type]  = type_counts.get(tc.test_type, 0) + 1
        env_counts[tc.environment] = env_counts.get(tc.environment, 0) + 1

    n_critical = sum(1 for tc in test_cases if tc.priority == "critical")
    n_high     = sum(1 for tc in test_cases if tc.priority == "high")
    n_medium   = sum(1 for tc in test_cases if tc.priority == "medium")

    lines: list[str] = []

    # Header
    lines += [
        "# AutoPragma — SWE.6 SW Qualification Test Specification",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Source SwRS | {metadata.get('document_id', '—')} v{metadata.get('version', '—')} |",
        f"| Project | {project_key} |",
        f"| Generated | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} |",
        f"| Total test cases | {len(test_cases)} |",
        f"| — Critical | {n_critical} |",
        f"| — High | {n_high} |",
        f"| — Medium | {n_medium} |",
        f"| HIL tests | {env_counts.get('HIL', 0)} |",
        f"| SIL tests | {env_counts.get('SIL', 0)} |",
        "",
        "> **Status:** AI-assisted draft. All test cases require human review and "
        "> approval before being treated as normative work products "
        "> (AutoPragma FR-015 / FR-007).",
        "",
    ]

    # Summary by type
    lines += [
        "## 1. Test Case Summary",
        "",
        "| Test Type | Count |",
        "|---|---|",
    ]
    for ttype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {_TYPE_LABEL.get(ttype, ttype.upper())} | {count} |")
    lines.append("")

    # Coverage traceability matrix
    lines += [
        "## 2. Traceability Matrix — SwRS → Test Cases",
        "",
        "| SwRS ID | SwRS Title | ASIL | Test Case ID | Test Type |",
        "|---|---|---|---|---|",
    ]
    for lnk in links:
        sw = swrs_by_id.get(lnk.swrs_id)
        tc = next((t for t in test_cases if t.id == lnk.test_case_id), None)
        if sw and tc:
            lines.append(
                f"| {lnk.swrs_id} | {sw.title[:60]} | {tc.asil.value} | "
                f"{lnk.test_case_id} | {_TYPE_LABEL.get(tc.test_type, tc.test_type)} |"
            )
    lines.append("")

    # Test cases
    lines += [
        "## 3. Test Cases (Draft — Pending Review)",
        "",
    ]

    for tc in sorted(test_cases, key=lambda t: _PRIORITY_ORDER.get(t.priority, 9)):
        asil_badge  = f"`{tc.asil.value}`"
        cyber_badge = " `CYBERSEC`" if tc.cybersecurity_relevant else ""
        type_badge  = f"`{_TYPE_LABEL.get(tc.test_type, tc.test_type)}`"
        prio_badge  = f"`{tc.priority.upper()}`"

        lines += [
            f"### {tc.id} — {tc.title}",
            "",
            f"**ASIL:** {asil_badge}{cyber_badge}  ",
            f"**Type:** {type_badge}  ",
            f"**Method:** {_METHOD_LABEL.get(tc.test_method, tc.test_method)}  ",
            f"**Environment:** `{tc.environment}`  ",
            f"**Priority:** {prio_badge}  ",
            f"**Coverage requirement:** `{tc.coverage_requirement}`  ",
            f"**Derived from SwRS:** `{tc.derived_from}`  ",
            f"**Status:** `{tc.status}`",
            "",
            "**Objective:**",
            f"> {tc.objective}",
            "",
            "**Preconditions:**",
        ]
        for pre in tc.preconditions:
            lines.append(f"- {pre}")
        lines.append("")

        lines += ["**Test Steps:**", ""]
        for step in tc.steps:
            lines += [
                f"| Step {step.step_number} | **Action:** {step.action} |",
                f"| | **Expected:** {step.expected_result} |",
            ]
        lines.append("")

        lines += [
            "**Pass criteria:**",
            f"> {tc.pass_criteria}",
            "",
            "**Fail criteria:**",
            f"> {tc.fail_criteria}",
            "",
            f"**Coverage tags:** {', '.join(f'`{t}`' for t in tc.coverage_tags)}",
            "",
            "---",
            "",
        ]

    path.write_text("\n".join(lines), encoding="utf-8")
