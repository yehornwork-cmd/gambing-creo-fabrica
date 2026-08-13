"""Shared game + intelligence context for factory orchestrators."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]


def game_root(game_id: str) -> Path:
    return REPO_ROOT / "library" / "games" / game_id


def load_competitor_hook(game_id: str) -> str:
    intel = game_root(game_id) / "intelligence" / "spytrend_snapshot.md"
    if not intel.is_file():
        return "Use verified gameplay footage — avoid fake star-rating affiliate tropes."
    for line in intel.read_text(encoding="utf-8").splitlines():
        if line.startswith("1. **"):
            return line.lstrip("1. ").strip()
    return "Differentiate with authentic screencast + compliance end card."


def load_scenario_summary(game_id: str) -> str:
    path = game_root(game_id) / "gameplay" / "pilot_ad_scenario.md"
    if not path.is_file():
        return "AD_B partial arc — no false FS claims."
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Cold-open"):
            return line.strip()
    return "AD_B partial arc — scatter tease without false bonus claim."


def load_capture_status(game_id: str) -> dict[str, Any]:
    manifest = game_root(game_id) / "MANIFEST.json"
    if not manifest.is_file():
        return {}
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return data.get("capture_status", {})


def enhancer_variables(
    *,
    game_id: str,
    game_title: str,
    aspect: str = "9:16",
    duration_sec: int | str = 30,
    locale: str = "en",
) -> dict[str, str]:
    capture = load_capture_status(game_id)
    recapture = capture.get("recapture_needed", False)
    return {
        "game_title": game_title,
        "game_id": game_id,
        "aspect": aspect,
        "duration_sec": str(duration_sec),
        "locale": locale,
        "competitor_hook": load_competitor_hook(game_id),
        "scenario_summary": load_scenario_summary(game_id),
        "capture_note": "FS re-capture pending" if recapture else "Capture segments verified",
    }


def brief_source_path(brief_arg: str) -> tuple[str, str]:
    """Return (brief_text, source_for_cli) from path or inline text."""
    path = Path(brief_arg)
    if path.is_file():
        return path.read_text(encoding="utf-8"), str(path)
    return brief_arg, brief_arg
