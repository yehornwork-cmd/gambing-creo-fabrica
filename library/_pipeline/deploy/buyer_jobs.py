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
    raw_path = str(params.get("video_path") or "").strip()
    video = Path(raw_path) if raw_path else out_dir / "source.mp4"

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
        compliance_allow=bool(params.get("compliance_allow")),
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
    """Gemini native-video rewrite of beats. Does not block the sync multiply plan."""
    video = Path(params.get("video_path") or "")
    analysis_id = params.get("analysis_id") or video.parent.name
    analysis_path = BUYER_ROOT / analysis_id / "analysis.json"
    if not video.is_file():
        raise FileNotFoundError(f"video not found: {video}")
    if str(CONSTRUCTOR) not in sys.path:
        sys.path.insert(0, str(CONSTRUCTOR))
    import deep_analyze  # noqa: E402

    if analysis_path.is_file():
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    else:
        analysis = analyze_upload.analyze(video=video, analysis_id=analysis_id, constructor_dir=CONSTRUCTOR)
    updated = deep_analyze.deepen(analysis, video, constructor_dir=CONSTRUCTOR)
    _write(analysis_path, updated)

    geos = params.get("geos") or []
    jobs = None
    summary = None
    if geos:
        repo_root = LIBRARY_ROOT.parent if (LIBRARY_ROOT.parent / "library").is_dir() else LIBRARY_ROOT
        jobs = multiply.multiply(
            analysis=updated,
            geos=list(geos),
            constructor_dir=CONSTRUCTOR,
            repo_root=repo_root,
            cta_ids=params.get("cta_ids"),
            compliance_allow=bool(params.get("compliance_allow")),
        )
        jobs_dir = BUYER_ROOT / analysis_id / "jobs"
        _write(jobs_dir / "jobs.json", jobs)
        summary = multiply.summary_payload(updated, jobs)
        _write(BUYER_ROOT / analysis_id / "summary.json", summary)

    signals_script = PIPELINE_ROOT / "orchestrator" / "signals" / "extract_signals.py"
    signals_status = "skipped"
    if signals_script.is_file():
        import subprocess

        out = BUYER_ROOT / analysis_id / "signals.json"
        proc = subprocess.run(
            [
                sys.executable,
                str(signals_script),
                "--video",
                str(video),
                "--out",
                str(out),
                "--skip-ocr",
            ],
            capture_output=True,
            text=True,
            cwd=str(signals_script.parent),
            env=os.environ.copy(),
            check=False,
        )
        signals_status = "success" if proc.returncode == 0 else "failed"

    return {
        "status": "success",
        "exit_code": 0,
        "analysis_status": updated.get("status"),
        "beats": len(updated.get("beats") or []),
        "signals": signals_status,
        "summary": summary,
    }
