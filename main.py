"""
AutoPragma — CLI entry point

Usage:
    python main.py swe1 --input <syrs_file.json>   [--output <dir>] [--project <key>]
    python main.py swe2 --input <swrs_output.json> [--output <dir>]

Examples:
    python main.py swe1 --input sample_data/sys_requirements.json
    python main.py swe2 --input output/swe1/swrs_output.json
"""

import argparse
import sys

from swe1 import derive_swrs, load_syrs, validate
from swe1 import write_outputs as swe1_write_outputs
from swe1.validate import finding_counts
from swe2 import allocate_swad, load_swrs_from_json
from swe2 import write_outputs as swe2_write_outputs


def cmd_swe1(args: argparse.Namespace) -> int:
    print(f"[AutoPragma] SWE.1 — loading SyRS from: {args.input}")

    try:
        metadata, syrs_items = load_syrs(args.input)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    project_key = args.project or metadata.get("project_key", "PROJ")
    print(f"[AutoPragma] Project: {project_key} | {len(syrs_items)} system requirements loaded")

    findings = validate(syrs_items)
    counts = finding_counts(findings)
    print(f"[AutoPragma] Validation: {counts['ERROR']} error(s), {counts['WARNING']} warning(s)")

    if counts["ERROR"] > 0:
        print("[AutoPragma] SWE.1 gate: FAIL — resolve errors before proceeding")
        for f in findings:
            if f.severity == "ERROR":
                print(f"  [ERROR][{f.rule_id}] {f.item_id}: {f.message}")
        print("[AutoPragma] Generating draft outputs despite errors (for review use only)")

    swrs_items, links = derive_swrs(syrs_items, project_key)
    print(f"[AutoPragma] Derived {len(swrs_items)} software requirement(s)")

    json_path, md_path = swe1_write_outputs(
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


def cmd_swe2(args: argparse.Namespace) -> int:
    print(f"[AutoPragma] SWE.2 — loading SwRS from: {args.input}")

    try:
        metadata, swrs_items = load_swrs_from_json(args.input)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    project_key = metadata.get("project_key", "PROJ")
    print(f"[AutoPragma] Project: {project_key} | {len(swrs_items)} SW requirements loaded")

    components, links = allocate_swad(swrs_items, project_key)
    print(f"[AutoPragma] Components derived: {len(components)}")
    for comp in components:
        alloc_count = len(comp.allocated_swrs)
        print(f"  [{comp.layer.upper():11s}] {comp.name:<20} {comp.asil.value:<7}  {alloc_count} SwRS")

    json_path, md_path, comp_puml, safety_puml = swe2_write_outputs(
        metadata=metadata,
        components=components,
        links=links,
        swrs_items=swrs_items,
        output_dir=args.output,
    )
    print(f"[AutoPragma] SwAD JSON       : {json_path}")
    print(f"[AutoPragma] SWE.2 report    : {md_path}")
    print(f"[AutoPragma] Component diagram: {comp_puml}")
    print(f"[AutoPragma] Safety diagram  : {safety_puml}")
    print(f"[AutoPragma] SWE.2 gate result: PASS")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autopragma",
        description="AutoPragma — ASPICE process automation platform",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p1 = sub.add_parser("swe1", help="SWE.1 Software Requirements Analysis")
    p1.add_argument("--input",   required=True, help="Path to SyRS JSON input file")
    p1.add_argument("--output",  default="output/swe1", help="Output directory")
    p1.add_argument("--project", default=None,  help="Project key override")

    p2 = sub.add_parser("swe2", help="SWE.2 Software Architectural Design")
    p2.add_argument("--input",  required=True, help="Path to swrs_output.json from SWE.1")
    p2.add_argument("--output", default="output/swe2", help="Output directory")

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "swe1":
        sys.exit(cmd_swe1(args))
    elif args.command == "swe2":
        sys.exit(cmd_swe2(args))
