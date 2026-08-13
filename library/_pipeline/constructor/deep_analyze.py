#!/usr/bin/env python3
"""Rewrite heuristic CreativeAnalysis beats using Gemini native video."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

CONSTRUCTOR_DIR = Path(__file__).resolve().parent

import analyze_upload  # noqa: E402
import gemini_video  # noqa: E402

PROMPT = """You are analyzing a short iGaming performance ad (the winning master).
Return JSON only:

{
  "language": "en|ru|pl|nl|de|fr|es|pt|ar|unknown",
  "spoken_cta": "short string or empty",
  "on_screen_cta": "short string or empty",
  "has_bonus_footage": false,
  "has_end_card": true,
  "overlay_safe": {"top_pct": 8, "bottom_pct": 18},
  "beats": [
    {
      "beat_id": "B01",
      "name": "motion_hook",
      "t_start": 0.0,
      "t_end": 3.2,
      "substitution_group": "motion_hook",
      "taxonomy_tags": ["motion_hook"]
    }
  ]
}

Rules:
- Beats must cover [0, DURATION_SEC] without gaps larger than 0.25s.
- Use these slot names when they fit: motion_hook, tumble_chain, scatter_bonus_4, multiplier_orb, win_climax, end_card.
- Do not claim a bonus/FS trigger unless it is visibly in the video (has_bonus_footage=true).
- Prefer 4–8 beats. Keep end_card as the last beat if a logo/CTA card exists, else a 1.5s tail.
- Times in seconds, 3 decimal places max.
DURATION_SEC=%%DURATION%%
TEMPLATE=%%TEMPLATE%%
"""


def _clamp_beats(raw: list[dict[str, Any]], duration: float, template: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not raw:
        return []
    duration = max(duration, 0.5)
    beats: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        try:
            start = float(item.get("t_start", 0))
            end = float(item.get("t_end", start))
        except (TypeError, ValueError):
            continue
        start = max(0.0, start)
        end = max(start + 0.2, end)
        tmpl = template[index] if index < len(template) else {}
        beats.append(
            {
                "beat_id": str(item.get("beat_id") or tmpl.get("beat_id") or f"B{index+1:02d}"),
                "name": str(item.get("name") or tmpl.get("name") or f"beat_{index+1}"),
                "t_start": round(start, 3),
                "t_end": round(min(end, duration), 3),
                "duration_sec": round(min(end, duration) - start, 3),
                "arc_slot_id": str(item.get("arc_slot_id") or tmpl.get("arc_slot_id") or ""),
                "substitution_group": str(
                    item.get("substitution_group") or tmpl.get("substitution_group") or "motion_hook"
                ),
                "taxonomy_tags": list(item.get("taxonomy_tags") or tmpl.get("taxonomy_tags") or []),
                "segment_id": tmpl.get("segment_id"),
                "source": "vlm",
            }
        )
    if not beats:
        return []
    beats.sort(key=lambda b: b["t_start"])
    beats[0]["t_start"] = 0.0
    beats[-1]["t_end"] = round(duration, 3)
    cursor = 0.0
    for beat in beats:
        if beat["t_start"] > cursor + 0.25:
            beat["t_start"] = round(cursor, 3)
        elif beat["t_start"] < cursor:
            beat["t_start"] = round(cursor, 3)
        if beat["t_end"] <= beat["t_start"]:
            beat["t_end"] = round(min(duration, beat["t_start"] + 0.4), 3)
        beat["duration_sec"] = round(beat["t_end"] - beat["t_start"], 3)
        cursor = beat["t_end"]
    beats[-1]["t_end"] = round(duration, 3)
    beats[-1]["duration_sec"] = round(beats[-1]["t_end"] - beats[-1]["t_start"], 3)
    return beats


def apply_gemini(
    analysis: dict[str, Any],
    parsed: dict[str, Any],
    template: list[dict[str, Any]],
) -> dict[str, Any]:
    duration = float((analysis.get("probe") or {}).get("duration_sec") or 0)
    beats = _clamp_beats(list(parsed.get("beats") or []), duration, template)
    if not beats:
        return analysis
    out = dict(analysis)
    out["beats"] = beats
    out["status"] = "ready"
    out["notes"] = "Beats from Gemini native video; heuristic map replaced."
    out["vlm"] = {
        "language": parsed.get("language"),
        "spoken_cta": parsed.get("spoken_cta"),
        "on_screen_cta": parsed.get("on_screen_cta"),
        "has_bonus_footage": bool(parsed.get("has_bonus_footage")),
        "has_end_card": bool(parsed.get("has_end_card", True)),
        "overlay_safe": parsed.get("overlay_safe") or {"top_pct": 8, "bottom_pct": 18},
        "model": gemini_video.GEMINI_VISION_MODEL,
    }
    return out


def deepen(analysis: dict[str, Any], video: Path, *, constructor_dir: Path | None = None) -> dict[str, Any]:
    constructor_dir = constructor_dir or CONSTRUCTOR_DIR
    api_key = gemini_video.load_gemini_api_key()
    if not api_key:
        analysis = dict(analysis)
        analysis["notes"] = (analysis.get("notes") or "") + " Gemini key missing; heuristic kept."
        return analysis
    if not video.is_file():
        return analysis
    scenario_id = analysis.get("scenario_id") or "AD_B"
    catalog = analyze_upload.load_json(constructor_dir / "scenarios" / "catalog.json")
    entry = next((s for s in catalog["scenarios"] if s["scenario_id"] == scenario_id), None)
    template: list[dict[str, Any]] = []
    if entry:
        scenario = analyze_upload.load_json(constructor_dir / "scenarios" / entry["file"])
        template = list(scenario.get("beats") or [])
    duration = float((analysis.get("probe") or {}).get("duration_sec") or 0)
    prompt = PROMPT.replace("%%DURATION%%", str(duration)).replace(
        "%%TEMPLATE%%", json.dumps(template, ensure_ascii=False)[:4000]
    )
    parsed = gemini_video.generate_json(api_key=api_key, prompt=prompt, video=video)
    if not parsed:
        analysis = dict(analysis)
        analysis["notes"] = (analysis.get("notes") or "") + " Gemini video call failed; heuristic kept."
        return analysis
    return apply_gemini(analysis, parsed, template)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deep-analyze a buyer master with Gemini native video.")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    analysis = json.loads(args.analysis.read_text(encoding="utf-8"))
    updated = deepen(analysis, args.video)
    out = args.out or args.analysis
    analyze_upload.write_json(out, updated)
    print(json.dumps({"status": updated.get("status"), "beats": len(updated.get("beats") or [])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
