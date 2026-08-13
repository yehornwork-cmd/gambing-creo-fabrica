#!/usr/bin/env python3
"""Batch dry-run or execute all catalog presets against a game brief."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE = REPO_ROOT / "library" / "_pipeline"
CATALOG = PIPELINE / "catalog" / "video_presets.json"
RUNS = PIPELINE / "runs"
PRESET_FACTORY = PIPELINE / "orchestrator" / "preset_factory.py"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_catalog() -> list[dict[str, Any]]:
    return json.loads(CATALOG.read_text(encoding="utf-8")).get("presets", [])


def run_preset(
    preset_id: str,
    brief: str,
    *,
    game_id: str,
    game_title: str,
    dry_run: bool,
) -> dict[str, Any]:
    cmd = [
        "python3",
        str(PRESET_FACTORY),
        "run",
        preset_id,
        brief,
        "--game-id",
        game_id,
        "--game-title",
        game_title,
    ]
    if dry_run:
        cmd.append("--dry-run")
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    result: dict[str, Any] = {"preset_id": preset_id, "exit_code": proc.returncode}
    if proc.returncode == 0:
        try:
            result["payload"] = json.loads(proc.stdout)
        except json.JSONDecodeError:
            result["stdout"] = proc.stdout.strip()
    else:
        result["stderr"] = (proc.stderr or proc.stdout).strip()
    return result


def cmd_batch(args: argparse.Namespace) -> int:
    presets = load_catalog()
    if args.family:
        presets = [p for p in presets if p.get("family") == args.family]

    run_id = f"{utc_stamp()}_preset_batch"
    run_dir = RUNS / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    failed = 0
    for preset in presets:
        pid = preset["id"]
        print(f"→ {pid}", file=sys.stderr)
        row = run_preset(
            pid,
            args.brief,
            game_id=args.game_id,
            game_title=args.game_title,
            dry_run=args.dry_run,
        )
        results.append(row)
        if row["exit_code"] != 0:
            failed += 1

    summary = {
        "run_id": run_id,
        "dry_run": args.dry_run,
        "game_id": args.game_id,
        "presets": len(results),
        "failed": failed,
        "results": results,
    }
    (run_dir / "batch.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (run_dir / "RUN.md").write_text(
        f"# Preset batch {run_id}\n\n"
        f"- presets: {len(results)}\n"
        f"- failed: {failed}\n"
        f"- dry_run: {args.dry_run}\n",
        encoding="utf-8",
    )
    print(json.dumps({"run_id": run_id, "failed": failed, "run_dir": str(run_dir)}, indent=2))
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch preset factory runs")
    parser.add_argument("brief", help="Brief markdown path")
    parser.add_argument("--game-id", default="vs20olympgate")
    parser.add_argument("--game-title", default="Gates of Olympus")
    parser.add_argument("--family", choices=["streamer", "ugc"], default=None)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--execute", action="store_true", help="Live API submission (requires keys)")
    args = parser.parse_args()
    if args.execute:
        args.dry_run = False
    return cmd_batch(args)


if __name__ == "__main__":
    raise SystemExit(main())
