#!/usr/bin/env python3
"""UGC streamer template runner — Higgsfield-backed preset execution."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
PIPELINE = REPO_ROOT / "library" / "_pipeline"
RUNS_DIR = PIPELINE / "runs"
CATALOG = PIPELINE / "catalog" / "video_presets.json"
LOAD_ENV = PIPELINE / "orchestrator" / "load_env.sh"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def find_preset(preset_id: str) -> dict[str, Any]:
    catalog = load_catalog()
    for preset in catalog.get("presets", []):
        if preset.get("id") == preset_id:
            return preset
    raise KeyError(f"Preset not found: {preset_id}")


def shell_with_env(inner: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-lc", f"source '{LOAD_ENV}' && {inner}"],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )


def load_competitor_hook(game_id: str) -> str:
    intel = REPO_ROOT / "library" / "games" / game_id / "intelligence" / "spytrend_snapshot.md"
    if not intel.is_file():
        return "Use verified gameplay footage — avoid fake star-rating affiliate tropes."
    for line in intel.read_text(encoding="utf-8").splitlines():
        if line.startswith("1. **"):
            return line.lstrip("1. ").strip()
    return "Differentiate with authentic screencast + compliance end card."


def run_enhancer(
    preset: dict[str, Any],
    brief: str,
    *,
    brief_source: str,
    game_title: str,
    game_id: str,
    dry_run: bool = False,
) -> str:
    flow = preset.get("enhancer_flow", "ugc-character")
    vars_json = json.dumps(
        {
            "game_title": game_title,
            "game_id": game_id,
            "aspect": preset.get("aspect", "9:16"),
            "duration_sec": str(preset.get("duration_sec", 30)),
            "locale": preset.get("locale", "en"),
            "competitor_hook": load_competitor_hook(game_id),
        }
    )
    no_llm = " --no-llm" if dry_run else ""
    inner = (
        f"python3 tools/creative_enhancer.py enhance {shlex.quote(flow)} {shlex.quote(brief_source)} "
        f"--vars {shlex.quote(vars_json)}{no_llm}"
    )
    proc = shell_with_env(inner)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "enhancer failed")
    return proc.stdout.strip()


def submit_higgsfield(preset: dict[str, Any], prompt: str, *, dry_run: bool) -> dict[str, Any]:
    endpoint = preset.get("higgsfield_endpoint")
    if not endpoint:
        raise ValueError(f"Preset {preset['id']} missing higgsfield_endpoint")

    arguments = dict(preset.get("default_arguments") or {})
    arguments.update({"prompt": prompt})
    if dry_run:
        return {"dry_run": True, "endpoint": endpoint, "arguments": arguments}

    inner = (
        "python3 tools/higgsfield_client.py subscribe "
        f"{shlex.quote(endpoint)} {shlex.quote(json.dumps(arguments))}"
    )
    proc = shell_with_env(inner)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "higgsfield subscribe failed")
    return json.loads(proc.stdout)


def write_run_log(run_dir: Path, payload: dict[str, Any]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "payload.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"# UGC run {payload['run_id']}",
        "",
        f"- **preset:** {payload['preset_id']}",
        f"- **game:** {payload.get('game_id', '—')}",
        f"- **dry_run:** {payload.get('dry_run', False)}",
        "",
        "## Enhanced prompt",
        "",
        payload.get("enhanced_prompt", ""),
        "",
        "## Higgsfield result",
        "",
        "```json",
        json.dumps(payload.get("higgsfield_result", {}), indent=2),
        "```",
        "",
    ]
    (run_dir / "RUN.md").write_text("\n".join(lines), encoding="utf-8")


def cmd_run(args: argparse.Namespace) -> int:
    preset = find_preset(args.preset or "ugc_streamer_template")
    brief_path = Path(args.brief)
    if brief_path.is_file():
        brief = brief_path.read_text(encoding="utf-8")
        brief_source = str(brief_path)
    else:
        brief = args.brief
        brief_source = args.brief

    run_id = f"{utc_stamp()}_{preset['id']}"
    run_dir = RUNS_DIR / run_id

    enhanced_prompt = run_enhancer(
        preset,
        brief,
        brief_source=brief_source,
        game_title=args.game_title,
        game_id=args.game_id,
        dry_run=args.dry_run,
    )
    hf_result = submit_higgsfield(preset, enhanced_prompt, dry_run=args.dry_run)

    payload = {
        "run_id": run_id,
        "preset_id": preset["id"],
        "game_id": args.game_id,
        "game_title": args.game_title,
        "dry_run": args.dry_run,
        "enhanced_prompt": enhanced_prompt,
        "higgsfield_result": hf_result,
    }
    write_run_log(run_dir, payload)
    print(json.dumps({"run_id": run_id, "run_dir": str(run_dir), **payload}, indent=2))
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    catalog = load_catalog()
    for preset in catalog.get("presets", []):
        if preset.get("family") == "ugc":
            print(f"{preset['id']}\t{preset.get('title', '')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Higgsfield UGC streamer template runner")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Enhance brief and submit to Higgsfield")
    p_run.add_argument("brief", help="Brief markdown or inline text")
    p_run.add_argument("--preset", default="ugc_streamer_template")
    p_run.add_argument("--game-id", default="vs20olympgate")
    p_run.add_argument("--game-title", default="Gates of Olympus")
    p_run.add_argument("--dry-run", action="store_true")
    p_run.set_defaults(func=cmd_run)

    sub.add_parser("list", help="List UGC presets").set_defaults(func=cmd_list)

    args = parser.parse_args()
    try:
        return args.func(args)
    except (KeyError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
