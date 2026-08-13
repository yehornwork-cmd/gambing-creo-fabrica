#!/usr/bin/env python3
"""Fast structural analysis of a buyer-uploaded master video.

Probe (ffprobe) + scale the live AD_B beat template onto the real duration.
This is the <10s path Forge needs before n8n finishes rendering. Deeper
signals / Gemini dual analysis can fill the same CreativeAnalysis later.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import uuid
from pathlib import Path
from typing import Any

CONSTRUCTOR_DIR = Path(__file__).resolve().parent
REPO_ROOT = CONSTRUCTOR_DIR.parents[2]

GAME_ALIASES = {
    "gates": "vs20olympgate",
    "olympus": "vs20olympgate",
    "vs20olympgate": "vs20olympgate",
    "sweet bonanza": "vs10bbbonanza",
    "bonanza": "vs10bbbonanza",
    "sugar rush": "vs20sugarrush",
    "starlight": "vs20starlight",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def guess_game_id(product: str | None) -> str:
    text = (product or "").strip().lower()
    if not text:
        return "vs20olympgate"
    for needle, game_id in GAME_ALIASES.items():
        if needle in text:
            return game_id
    return "vs20olympgate"


def classify_format(width: int, height: int) -> tuple[str, str]:
    if width <= 0 or height <= 0:
        return "9x16", "9:16"
    ratio = width / height
    if ratio < 0.85:
        return "9x16", "9:16"
    if ratio > 1.2:
        return "16x9", "16:9"
    return "1x1", "1:1"


def probe_video(path: Path) -> dict[str, Any]:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"ffprobe failed on {path}")
    payload = json.loads(proc.stdout or "{}")
    streams = payload.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fmt = payload.get("format") or {}
    fps_raw = str(video.get("avg_frame_rate") or "30/1")
    try:
        num, den = fps_raw.split("/", 1)
        fps = float(num) / float(den) if float(den) else 30.0
    except (ValueError, ZeroDivisionError):
        fps = 30.0
    width = int(video.get("width") or 0)
    height = int(video.get("height") or 0)
    duration = float(fmt.get("duration") or video.get("duration") or 0)
    fmt_id, aspect = classify_format(width, height)
    return {
        "duration_sec": round(duration, 3),
        "width": width,
        "height": height,
        "fps": round(fps, 3),
        "has_audio": audio is not None,
        "aspect": aspect,
        "format": fmt_id,
    }


def scale_scenario_beats(
    scenario: dict[str, Any],
    duration_sec: float,
) -> list[dict[str, Any]]:
    template = list(scenario.get("beats") or [])
    if not template:
        return []
    raw_total = sum(float(b.get("duration_sec") or 0) for b in template) or 1.0
    target = duration_sec if duration_sec > 0.5 else raw_total
    scale = target / raw_total
    cursor = 0.0
    beats: list[dict[str, Any]] = []
    for index, beat in enumerate(template):
        if index == len(template) - 1:
            end = target
        else:
            end = cursor + float(beat.get("duration_sec") or 0) * scale
        start = cursor
        beats.append(
            {
                "beat_id": beat["beat_id"],
                "name": beat.get("name", beat["beat_id"]),
                "t_start": round(start, 3),
                "t_end": round(end, 3),
                "duration_sec": round(max(end - start, 0.0), 3),
                "arc_slot_id": beat.get("arc_slot_id", ""),
                "substitution_group": beat.get("substitution_group", ""),
                "taxonomy_tags": list(beat.get("taxonomy_tags") or []),
                "segment_id": beat.get("segment_id"),
                "source": "heuristic",
            }
        )
        cursor = end
    return beats


def pick_scenario_id(duration_sec: float, requested: str | None = None) -> str:
    """Short ads use the live hook/mechanic arcs; 18s+ stays on AD_B."""
    if requested and requested != "AD_B":
        return requested
    if duration_sec > 0 and duration_sec < 8:
        return "AD_HOOK_ONLY"
    if duration_sec >= 8 and duration_sec < 18:
        return "AD_MECHANIC_SHOWCASE"
    return requested or "AD_B"


def analyze(
    *,
    video: Path,
    product: str = "",
    game_id: str | None = None,
    scenario_id: str = "AD_B",
    source_url: str | None = None,
    original_name: str | None = None,
    analysis_id: str | None = None,
    constructor_dir: Path | None = None,
) -> dict[str, Any]:
    constructor_dir = constructor_dir or CONSTRUCTOR_DIR
    if not video.is_file():
        raise FileNotFoundError(f"video not found: {video}")

    probe = probe_video(video)
    scenario_id = pick_scenario_id(probe["duration_sec"], scenario_id)
    catalog = load_json(constructor_dir / "scenarios" / "catalog.json")
    entry = next((s for s in catalog["scenarios"] if s["scenario_id"] == scenario_id), None)
    if entry is None:
        raise FileNotFoundError(f"Unknown scenario_id: {scenario_id}")
    scenario = load_json(constructor_dir / "scenarios" / entry["file"])

    aid = analysis_id or uuid.uuid4().hex[:12]
    resolved_game = game_id or guess_game_id(product)
    return {
        "analysis_id": aid,
        "schema_version": "1.0.0",
        "parent_creative_id": aid,
        "source": {
            "kind": "upload",
            "path": str(video),
            "url": source_url,
            "original_name": original_name or video.name,
        },
        "probe": {
            "duration_sec": probe["duration_sec"],
            "width": probe["width"],
            "height": probe["height"],
            "fps": probe["fps"],
            "has_audio": probe["has_audio"],
            "aspect": probe["aspect"],
        },
        "format": probe["format"],
        "game_id": resolved_game,
        "scenario_id": scenario_id,
        "product": product or "",
        "beats": scale_scenario_beats(scenario, probe["duration_sec"]),
        "status": "heuristic",
        "notes": "Beat times are AD_B slots scaled to the master duration. Swap with signals/VLM when deep analysis finishes.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze a buyer-uploaded master into CreativeAnalysis JSON.")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--product", default="")
    parser.add_argument("--game-id", default=None)
    parser.add_argument("--scenario-id", default="AD_B")
    parser.add_argument("--source-url", default=None)
    parser.add_argument("--out", type=Path, default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    analysis = analyze(
        video=args.video,
        product=args.product,
        game_id=args.game_id,
        scenario_id=args.scenario_id,
        source_url=args.source_url,
    )
    if args.out:
        write_json(args.out, analysis)
        print(f"wrote {args.out}")
    else:
        print(json.dumps(analysis, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
