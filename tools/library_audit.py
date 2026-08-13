#!/usr/bin/env python3
"""Audit library JSON files for remaining absolute macOS paths."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ABSOLUTE_PATH_PATTERN = re.compile(r"/Users/[^\s\"'\\]+")


def scan_file(json_file: Path) -> list[tuple[int, str]]:
    """Return list of (line_number, matched_path) for a file."""
    findings: list[tuple[int, str]] = []

    with json_file.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            for match in ABSOLUTE_PATH_PATTERN.finditer(line):
                findings.append((line_number, match.group(0)))

    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan library/ JSON files for remaining absolute /Users/ paths."
    )
    parser.add_argument(
        "--library-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "library",
        help="Library directory to scan (default: ../library)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    library_dir: Path = args.library_dir

    if not library_dir.is_dir():
        print(f"error: library directory not found: {library_dir}", file=sys.stderr)
        return 2

    json_files = sorted(library_dir.rglob("*.json"))
    if not json_files:
        print(f"No JSON files found under {library_dir}")
        return 0

    issues_found = False

    for json_file in json_files:
        findings = scan_file(json_file)
        for line_number, matched_path in findings:
            issues_found = True
            print(f"{json_file}:{line_number}: {matched_path}")

    if issues_found:
        return 1

    print("Clean: no absolute /Users/ paths found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
