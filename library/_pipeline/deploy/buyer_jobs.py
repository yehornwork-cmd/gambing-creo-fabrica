#!/usr/bin/env python3
"""Buyer ingest → analyze → multiply. Used by the Hetzner VOD worker.

Fast path is ffprobe + constructor explode (seconds). Optional deep analysis
reuses extract_signals --skip-ocr on the saved master.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

PIPELINE_ROOT = Path(os.environ.get("PIPELINE_ROOT", Path(__file__).resolve().parent.parent))
LIBRARY_ROOT = Path(os.environ.get("LIBRARY_ROOT", PIPELINE_ROOT.parent))
CONSTRUCTOR = PIPELINE_ROOT / "constructor"
BUYER_ROOT = PIPELINE_ROOT / "buyer_uploads"

if str(CONSTRUCTOR) not in sys.path:
    sys.path.insert(0, str(CONSTRUCTOR))

ALLOWED_HOSTS = {
    "forge",
    "forge-forge-1",
    "forge.vizioner.xyz",
    "render.vizioner.xyz",
}

import analyze_upload  # noqa: E402
import multiply  # noqa: E402


def _is_allowed_url(raw: str) -> bool:
    try:
        url = urlparse(raw)
    except ValueError:
        return False
    if url.scheme not in ("http", "https"):
        return False
    host = (url.hostname or "").lower()
    if host in ALLOWED_HOSTS:
        return True
    if host.endswith(".vizioner.xyz"):
        return True
    return False


def _download(url: str, dest: Path) -> None:
    if not _is_allowed_url(url):
        raise ValueError(f"source_url host is not allowed: {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": "forge-buyer-multiply/1.0"})
    with urlopen(req, timeout=120) as resp:  # noqa: S310  — host allowlisted above
        dest.write_bytes(resp.read())


def _write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_buyer_multiply(params: dict[str, Any]) -> dict[str, Any]:
    geos = params.get("geos") or []
    if isinstance(geos, str):
        geos = [g.strip() for g in geos.split(",") if g.strip()]
    if not geos:
        raise ValueError("geos required")

    analysis_id = params.get("analysis_id") or uuid.uuid4().hex[:12]
    out_dir = BUYER_ROOT / analysis_id
    video = Path(params["video_path"]) if params.get("video_path") else out_dir / "source.mp4"

    if params.get("source_url") and not video.is_file():
        _download(str(params["source_url"]), video)
    if not video.is_file():
        raise FileNotFoundError("master video missing (need source_url or video_path)")

    analysis = analyze_upload.analyze(
        video=video,
        product=str(params.get("product") or ""),
        game_id=params.get("game_id") or None,
        source_url=params.get("source_url"),
        original_name=params.get("original_name"),
        analysis_id=analysis_id,
        constructor_dir=CONSTRUCTOR,
    )
    repo_root = LIBRARY_ROOT.parent if (LIBRARY_ROOT.parent / "library").is_dir() else LIBRARY_ROOT
    jobs = multiply.multiply(
        analysis=analysis,
        geos=list(geos),
        constructor_dir=CONSTRUCTOR,
        repo_root=repo_root,
        cta_ids=params.get("cta_ids"),
    )

    jobs_dir = out_dir / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    _write(out_dir / "analysis.json", analysis)
    _write(jobs_dir / "jobs.json", jobs)
    summary = multiply.summary_payload(analysis, jobs)
    _write(out_dir / "summary.json", summary)

    return {
        "status": "success",
        "exit_code": 0,
        "analysis_id": analysis_id,
        "video_path": str(video),
        "analysis": analysis,
        "jobs": jobs,
        "summary": summary,
    }


def run_buyer_deep(params: dict[str, Any]) -> dict[str, Any]:
    """Optional motion/scene pass. Does not block the buyer-facing multiply plan."""
    video = Path(params.get("video_path") or "")
    analysis_id = params.get("analysis_id") or video.parent.name
    if not video.is_file():
        raise FileNotFoundError(f"video not found: {video}")
    out = BUYER_ROOT / analysis_id / "signals.json"
    script = PIPELINE_ROOT / "orchestrator" / "signals" / "extract_signals.py"
    if not script.is_file():
        return {"status": "skipped", "reason": "extract_signals.py missing", "exit_code": 0}
    import subprocess

    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--video",
            str(video),
            "--out",
            str(out),
            "--skip-ocr",
        ],
        capture_output=True,
        text=True,
        cwd=str(script.parent),
        env=os.environ.copy(),
        check=False,
    )
    return {
        "status": "success" if proc.returncode == 0 else "failed",
        "exit_code": proc.returncode,
        "signals_path": str(out) if proc.returncode == 0 else None,
        "output_tail": ((proc.stdout or "") + (proc.stderr or ""))[-8000:],
    }
