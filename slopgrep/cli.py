from __future__ import annotations

import argparse
import sys

from .core import format_report_text, load_rules, reports_to_json, scan_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="slopgrep", description="Scan text for AI-writing tropes")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan files or directories")
    scan_parser.add_argument("paths", nargs="+", help="Files or directories to scan")
    scan_parser.add_argument("--config", help="Custom TOML rule pack")
    scan_parser.add_argument("--json", action="store_true", help="Emit JSON")
    scan_parser.add_argument("--include", action="append", default=[], help="Include glob")
    scan_parser.add_argument("--exclude", action="append", default=[], help="Exclude glob")
    scan_parser.add_argument("--threshold", type=int, default=0, help="Minimum slop score to report")
    scan_parser.add_argument("--max-findings", type=int, default=100, help="Cap findings per file")

    rules_parser = subparsers.add_parser("rules", help="List active rules")
    rules_parser.add_argument("--config", help="Custom TOML rule pack")
    rules_parser.add_argument("--json", action="store_true", help="Emit JSON")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        rules = load_rules(getattr(args, "config", None))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"slopgrep: {exc}\n")

    if args.command == "rules":
        if args.json:
            import json

            print(
                json.dumps(
                    [
                        {
                            "id": rule.id,
                            "severity": rule.severity,
                            "message": rule.message,
                            "category": rule.category,
                            "weight": rule.weight,
                            "pattern": rule.pattern,
                        }
                        for rule in rules
                    ],
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            for rule in rules:
                print(f"{rule.id} [{rule.severity}] ({rule.category}, weight={rule.weight}) - {rule.message}")
        return 0

    reports = scan_paths(
        args.paths,
        rules,
        includes=args.include,
        excludes=args.exclude,
        max_findings=args.max_findings,
        threshold=args.threshold,
    )
    if args.json:
        print(reports_to_json(reports))
    else:
        print(format_report_text(reports, threshold=args.threshold))
    return 1 if reports else 0


if __name__ == "__main__":
    raise SystemExit(main())
