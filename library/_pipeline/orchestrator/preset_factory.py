#!/usr/bin/env python3
"""Preset factory orchestrator — list, validate, and run catalog video presets."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
PIPELINE = REPO_ROOT / "library" / "_pipeline"
CATALOG = PIPELINE / "catalog" / "video_presets.json"
LOAD_ENV = PIPELINE / "orchestrator" / "load_env.sh"


def load_catalog() -> dict[str, Any]:
    if not CATALOG.is_file():
        raise FileNotFoundError(f"Catalog missing: {CATALOG}")
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def validate_preset(preset: dict[str, Any]) -> list[str]:
    required = ["id", "title", "family", "enhancer_flow", "aspect", "duration_sec"]
    errors: list[str] = []
    for field in required:
        if not preset.get(field):
            errors.append(f"{preset.get('id', '?')}: missing {field}")
    if preset.get("provider") == "higgsfield" and not preset.get("higgsfield_endpoint"):
        errors.append(f"{preset['id']}: higgsfield preset missing endpoint")
    if preset.get("provider") == "fal" and not preset.get("fal_model_id"):
        errors.append(f"{preset['id']}: fal preset missing fal_model_id")
    flow = preset.get("enhancer_flow", "")
    prompt_path = PIPELINE / "enhancer" / "prompts" / f"{flow}.md"
    if flow and not prompt_path.is_file():
        errors.append(f"{preset.get('id', '?')}: prompt template missing for flow {flow}")
    return errors


def cmd_list(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    presets = catalog.get("presets", [])
    if args.family:
        presets = [p for p in presets if p.get("family") == args.family]
    for preset in presets:
        print(
            f"{preset['id']}\t{preset.get('family', '')}\t{preset.get('provider', '')}\t{preset.get('title', '')}"
        )
    return 0


def cmd_validate(_: argparse.Namespace) -> int:
    catalog = load_catalog()
    all_errors: list[str] = []
    for preset in catalog.get("presets", []):
        all_errors.extend(validate_preset(preset))
    if all_errors:
        for err in all_errors:
            print(err, file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "presets": len(catalog.get("presets", []))}, indent=2))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    preset = next((p for p in catalog.get("presets", []) if p["id"] == args.preset_id), None)
    if preset is None:
        print(f"ERROR: unknown preset {args.preset_id}", file=sys.stderr)
        return 1

    family = preset.get("family")
    if family == "ugc":
        runner = PIPELINE / "orchestrator" / "higgsfield_ugc.py"
        cmd = [
            "python3",
            str(runner),
            "run",
            args.brief,
            "--preset",
            args.preset_id,
            "--game-id",
            args.game_id,
            "--game-title",
            args.game_title,
        ]
        if args.dry_run:
            cmd.append("--dry-run")
        return subprocess.call(cmd, cwd=REPO_ROOT)

    # Streamer and generic presets: enhance locally, optionally submit.
    enhancer = REPO_ROOT / "tools" / "creative_enhancer.py"
    cmd = [
        "python3",
        str(enhancer),
        "enhance",
        preset["enhancer_flow"],
        args.brief,
        "--vars",
        json.dumps(
            {
                "game_title": args.game_title,
                "game_id": args.game_id,
                "aspect": preset.get("aspect", "9:16"),
                "duration_sec": str(preset.get("duration_sec", 30)),
                "locale": preset.get("locale", "en"),
            }
        ),
    ]
    if args.dry_run:
        cmd.append("--no-llm")
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout, file=sys.stderr)
        return proc.returncode
    print(proc.stdout)
    return 0


def shell_with_env(inner: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-lc", f"source '{LOAD_ENV}' && {inner}"],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )


def cmd_check_auth(_: argparse.Namespace) -> int:
    checks = [
        "python3 tools/higgsfield_client.py check-auth",
        "python3 tools/perplexity_client.py check-auth",
        "python3 tools/fal_client.py check-auth",
    ]
    results: dict[str, Any] = {}
    exit_code = 0
    for inner in checks:
        name = Path(inner.split()[1]).stem
        proc = shell_with_env(inner)
        try:
            payload = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            payload = {"ok": False, "message": proc.stdout or proc.stderr}
        results[name] = payload
        if not payload.get("ok"):
            exit_code = 1
    print(json.dumps(results, indent=2))
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Factory preset orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List catalog presets")
    p_list.add_argument("--family", choices=["streamer", "ugc", "broll"], default=None)
    p_list.set_defaults(func=cmd_list)

    sub.add_parser("validate", help="Validate catalog and prompt templates").set_defaults(func=cmd_validate)
    sub.add_parser("check-auth", help="Check all media connector credentials").set_defaults(func=cmd_check_auth)

    p_run = sub.add_parser("run", help="Run a catalog preset against a brief")
    p_run.add_argument("preset_id")
    p_run.add_argument("brief", help="Brief text or markdown path")
    p_run.add_argument("--game-id", default="vs20olympgate")
    p_run.add_argument("--game-title", default="Gates of Olympus")
    p_run.add_argument("--dry-run", action="store_true")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args()
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
