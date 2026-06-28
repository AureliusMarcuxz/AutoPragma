"""
Generate SWE.1 outputs:
  - swrs_output.json   — machine-readable SwRS with traceability links
  - swe1_report.md     — human-readable review summary for gate evidence
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .models import SwRSItem, TraceabilityLink, ValidationFinding
from .validate import finding_counts


def write_outputs(
    metadata: dict,
    swrs_items: list[SwRSItem],
    links: list[TraceabilityLink],
    findings: list[ValidationFinding],
    output_dir: str,
) -> tuple[Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "swrs_output.json"
    md_path = out / "swe1_report.md"

    _write_json(metadata, swrs_items, links, findings, json_path)
    _write_markdown(metadata, swrs_items, links, findings, md_path)

    return json_path, md_path


# ── JSON output ──────────────────────────────────────────────────────────────

def _write_json(
    metadata: dict,
    swrs_items: list[SwRSItem],
    links: list[TraceabilityLink],
    findings: list[ValidationFinding],
    path: Path,
) -> None:
    payload = {
        "metadata": {
            **metadata,
            "generated_by": "AutoPragma SWE.1 processor",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "swrs_count": len(swrs_items),
            "traceability_links": len(links),
        },
        "validation": {
            "findings_count": finding_counts(findings),
            "findings": [asdict(f) for f in findings],
        },
        "requirements": [_swrs_to_dict(item) for item in swrs_items],
        "traceability": [asdict(link) for link in links],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _swrs_to_dict(item: SwRSItem) -> dict:
    d = asdict(item)
    d["asil"] = item.asil.value
    d["verification_method"] = item.verification_method.value
    return d


# ── Markdown report ───────────────────────────────────────────────────────────

def _write_markdown(
    metadata: dict,
    swrs_items: list[SwRSItem],
    links: list[TraceabilityLink],
    findings: list[ValidationFinding],
    path: Path,
) -> None:
    counts = finding_counts(findings)
    errors = [f for f in findings if f.severity == "ERROR"]
    warnings = [f for f in findings if f.severity == "WARNING"]
    gate_result = "FAIL" if errors else "PASS"

    lines: list[str] = []

    # Header
    lines += [
        f"# AutoPragma — SWE.1 Process Report",
        f"",
        f"| Field | Value |",
        f"|---|---|",
        f"| Source SyRS | {metadata.get('document_id', '—')} v{metadata.get('version', '—')} |",
        f"| Project | {metadata.get('project_key', '—')} |",
        f"| Generated | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} |",
        f"| SyRS items processed | {len(links)} |",
        f"| SwRS items generated | {len(swrs_items)} |",
        f"| **SWE.1 Gate** | **{gate_result}** |",
        f"",
    ]

    # Validation summary
    lines += [
        "## 1. Validation Summary",
        "",
        f"| Severity | Count |",
        f"|---|---|",
        f"| ERROR | {counts['ERROR']} |",
        f"| WARNING | {counts['WARNING']} |",
        f"| INFO | {counts.get('INFO', 0)} |",
        "",
    ]

    if errors:
        lines += ["### Errors (must resolve before gate passes)", ""]
        for f in errors:
            lines.append(f"- **[{f.rule_id}]** `{f.item_id}` — {f.message}")
        lines.append("")

    if warnings:
        lines += ["### Warnings (review recommended)", ""]
        for f in warnings:
            lines.append(f"- **[{f.rule_id}]** `{f.item_id}` — {f.message}")
        lines.append("")

    if not findings:
        lines += ["All completeness and consistency checks passed.", ""]

    # Traceability matrix
    lines += [
        "## 2. Traceability Matrix (SyRS → SwRS)",
        "",
        "| SyRS ID | SwRS ID | Link Type |",
        "|---|---|---|",
    ]
    for link in links:
        lines.append(f"| {link.source_id} | {link.target_id} | {link.link_type} |")
    lines.append("")

    # SwRS items
    lines += [
        "## 3. Generated Software Requirements (Draft — Pending Review)",
        "",
        "> **Status:** AI-assisted draft. All items require human review and approval",
        "> before being treated as normative work products (AutoPragma FR-015 / FR-007).",
        "",
    ]

    for item in swrs_items:
        asil_badge = f"`{item.asil.value}`"
        cyber_badge = " `CYBERSEC`" if item.cybersecurity_relevant else ""
        lines += [
            f"### {item.id} — {item.title}",
            f"",
            f"**ASIL:** {asil_badge}{cyber_badge}  ",
            f"**Type:** {item.type}  ",
            f"**Verification:** {item.verification_method.value}  ",
            f"**Derived from:** {item.derived_from}  ",
            f"**Status:** {item.status}",
            f"",
            f"**Requirement:**",
            f"> {item.text}",
            f"",
            f"**Rationale:**  ",
            f"{item.rationale}",
            f"",
            f"**Tags:** {', '.join(item.tags) if item.tags else '—'}",
            f"",
            "---",
            "",
        ]

    path.write_text("\n".join(lines), encoding="utf-8")
