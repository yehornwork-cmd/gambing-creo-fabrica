#!/usr/bin/env python3
"""QC lint for CreativeJobs — fail a batch row on blocked claims (F4.1)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CONSTRUCTOR_DIR = Path(__file__).resolve().parent

GUARANTEED_WIN = re.compile(
    r"\b(guaranteed win|100%\s*win|always win|гарантированн\w*\s*выигрыш)\b",
    re.IGNORECASE,
)
FALSE_BONUS = re.compile(
    r"\b(free spins (unlocked|triggered)|fs triggered|бонус уже|выбил(а|и)?\s*бонус)\b",
    re.IGNORECASE,
)


def _job_text(job: dict[str, Any]) -> str:
    variables = (job.get("render") or {}).get("variables") or {}
    parts = [str(v) for v in variables.values()]
    parts.append(str(job.get("blocked_reason") or ""))
    return " ".join(parts)


def lint_job(job: dict[str, Any], *, bonus_in_source: bool = False) -> dict[str, Any]:
    """Return a copy. Sets status=blocked when copy violates blocked_claims."""
    out = json.loads(json.dumps(job))
    text = _job_text(out)
    reasons: list[str] = []
    if GUARANTEED_WIN.search(text):
        reasons.append("blocked_claim:guaranteed_win")
    if not bonus_in_source and FALSE_BONUS.search(text):
        reasons.append("blocked_claim:bonus_triggered_when_not_in_capture")
    if out.get("status") == "blocked" and out.get("blocked_reason"):
        return out
    if reasons:
        out["status"] = "blocked"
        out["blocked_reason"] = ";".join(reasons)
    return out


def lint_jobs(jobs: list[dict[str, Any]], *, bonus_in_source: bool = False) -> list[dict[str, Any]]:
    return [lint_job(job, bonus_in_source=bonus_in_source) for job in jobs]


def ready_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [job for job in jobs if job.get("status") != "blocked"]
