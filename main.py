"""
AutoPragma — CLI entry point

Usage:
    python main.py swe1 --input <syrs_file.json> [--output <dir>] [--project <key>]

Example:
    python main.py swe1 --input sample_data/sys_requirements.json
"""

import argparse
import sys

from swe1 import derive_swrs, load_syrs, validate, write_outputs
from swe1.validate import finding_counts


def cmd_swe1(args: argparse.Namespace) -> int:
    print(f"[AutoPragma] SWE.1 — loading SyRS from: {args.input}")

    try:
        metadata, syrs_items = load_syrs(args.input)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    project_key = args.project or metadata.get("project_key", "PROJ")
    print(f"[AutoPragma] Project: {project_key} | {len(syrs_items)} system requirements loaded")

    # Validate SyRS completeness and consistency
    findings = validate(syrs_items)
    counts = finding_counts(findings)
    print(
        f"[AutoPragma] Validation: {counts['ERROR']} error(s), "
        f"{counts['WARNING']} warning(s)"
    )

    if counts["ERROR"] > 0:
        print("[AutoPragma] SWE.1 gate: FAIL — resolve errors before proceeding")
        for f in findings:
            if f.severity == "ERROR":
                print(f"  [ERROR][{f.rule_id}] {f.item_id}: {f.message}")
        # Still derive and write outputs so the author can see the draft
        print("[AutoPragma] Generating draft outputs despite errors (for review use only)")

    # Derive SwRS items
    swrs_items, links = derive_swrs(syrs_items, project_key)
    print(f"[AutoPragma] Derived {len(swrs_items)} software requirement(s)")

    # Write outputs
    json_path, md_path = write_outputs(
        metadata=metadata,
        swrs_items=swrs_items,
        links=links,
        findings=findings,
        output_dir=args.output,
    )
    print(f"[AutoPragma] SwRS JSON     : {json_path}")
    print(f"[AutoPragma] SWE.1 report  : {md_path}")

    gate = "PASS" if counts["ERROR"] == 0 else "FAIL"
    print(f"[AutoPragma] SWE.1 gate result: {gate}")
    return 0 if gate == "PASS" else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autopragma",
        description="AutoPragma — ASPICE process automation platform",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    swe1 = sub.add_parser("swe1", help="SWE.1 Software Requirements Analysis")
    swe1.add_argument("--input",   required=True, help="Path to SyRS JSON input file")
    swe1.add_argument("--output",  default="output/swe1", help="Output directory")
    swe1.add_argument("--project", default=None,  help="Project key override")

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "swe1":
        sys.exit(cmd_swe1(args))
