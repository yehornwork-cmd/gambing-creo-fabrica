#!/usr/bin/env python3
"""Normalize absolute macOS paths in JSON files to relative library/ paths."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PREFIX_LIBRARY = "/Users/yehor/Documents/nanobanana_generated/бузинес/library/"
PREFIX_ROOT = "/Users/yehor/Documents/nanobanana_generated/бузинес/"


def normalize_path_value(value: str) -> tuple[str, int]:
    """Replace known absolute prefixes in a string. Returns (new_value, replacement_count)."""
    count = 0
    new_value = value

    if PREFIX_LIBRARY in new_value:
        occurrences = new_value.count(PREFIX_LIBRARY)
        new_value = new_value.replace(PREFIX_LIBRARY, "library/")
        count += occurrences

    while PREFIX_ROOT in new_value:
        new_value = new_value.replace(PREFIX_ROOT, "library/", 1)
        count += 1

    return new_value, count


def normalize_json_obj(obj: Any) -> tuple[Any, int]:
    """Recursively normalize path strings inside a JSON structure."""
    if isinstance(obj, dict):
        total = 0
        normalized: dict[str, Any] = {}
        for key, value in obj.items():
            new_value, count = normalize_json_obj(value)
            normalized[key] = new_value
            total += count
        return normalized, total

    if isinstance(obj, list):
        total = 0
        normalized: list[Any] = []
        for item in obj:
            new_item, count = normalize_json_obj(item)
            normalized.append(new_item)
            total += count
        return normalized, total

    if isinstance(obj, str):
        new_value, count = normalize_path_value(obj)
        return new_value, count

    return obj, 0


def process_file(input_path: Path, output_path: Path | None) -> int:
    """Normalize one JSON file. Returns number of replacements made."""
    with input_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    normalized, replacements = normalize_json_obj(data)
    if replacements == 0:
        return 0

    destination = output_path or input_path
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(normalized, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    return replacements


def collect_json_files(path: Path, recursive: bool) -> list[Path]:
    """Collect JSON files from a file or directory input."""
    if path.is_file():
        if path.suffix.lower() != ".json":
            raise ValueError(f"Input file is not a JSON file: {path}")
        return [path]

    if not path.is_dir():
        raise FileNotFoundError(f"Input path does not exist: {path}")

    pattern = "**/*.json" if recursive else "*.json"
    return sorted(path.glob(pattern))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replace absolute macOS library paths with relative library/ paths in JSON files."
    )
    parser.add_argument("input", type=Path, help="Input JSON file or directory")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional output file (single-file mode only; defaults to in-place update)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Process all .json files in a directory recursively",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_path: Path = args.input
    output_path: Path | None = args.output

    if output_path is not None and (args.recursive or input_path.is_dir()):
        print("error: --output is only supported for single-file mode", file=sys.stderr)
        return 2

    try:
        json_files = collect_json_files(input_path, args.recursive or input_path.is_dir())
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not json_files:
        print("No JSON files found.")
        return 0

    total_replacements = 0
    affected_files: list[str] = []

    for json_file in json_files:
        replacements = process_file(json_file, output_path if len(json_files) == 1 else None)
        if replacements:
            total_replacements += replacements
            affected_files.append(str(json_file))

    print(f"Paths replaced: {total_replacements}")
    if affected_files:
        print("Files affected:")
        for file_path in affected_files:
            print(f"  - {file_path}")
    else:
        print("Files affected: none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
