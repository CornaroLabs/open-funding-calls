"""Command line: python -m open_funding_calls FILE [FILE ...] [--json] [--strict]"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .validator import load_schema, validate_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ofc-validate", description="Validate Open Funding Calls records.")
    parser.add_argument("paths", nargs="+", type=Path, help="JSON or JSONL files, or directories")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = parser.parse_args(argv)

    files: list[Path] = []
    for p in args.paths:
        files.extend(sorted(p.rglob("*.json*")) if p.is_dir() else [p])

    schema = load_schema()
    report, failed = {}, False
    for f in files:
        issues = validate_file(f, schema)
        report[str(f)] = issues
        if any(i.severity == "error" or args.strict for i in issues):
            failed = True

    if args.json:
        print(json.dumps({k: [asdict(i) for i in v] for k, v in report.items()}, indent=2, ensure_ascii=False))
    else:
        for f, issues in report.items():
            print(f"{'FAIL' if any(i.severity == 'error' for i in issues) else 'ok  '} {f}")
            for i in issues:
                print(f"     {i}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
