#!/usr/bin/env python3
"""FastAPI routes for the Forge buyer loop. Mounted from remote_worker.py."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field


class BuyerMultiplyRequest(BaseModel):
    source_url: str | None = None
    video_path: str | None = None
    geos: list[str] = Field(min_length=1, max_length=25)
    product: str = ""
    game_id: str | None = None
    original_name: str | None = None
    deep_analyze: bool = True
    cta_ids: list[str] | None = None
    analysis_id: str | None = None


def job_previews(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for job in jobs:
        variables = (job.get("render") or {}).get("variables") or {}
        rows.append(
            {
                "job_id": job["job_id"],
                "geo": variables.get("forge_geo") or job.get("geo"),
                "locale": job.get("locale"),
                "cta_id": job.get("cta_id"),
                "format": job.get("format"),
                "status": job.get("status"),
                "cta_main": variables.get("cta_main"),
                "disclaimer": variables.get("disclaimer"),
            }
        )
    return rows


def register(
    app: FastAPI,
    *,
    verify_token,
    enqueue,
) -> None:
    @app.post("/jobs/buyer/multiply")
    def buyer_multiply(
        payload: BuyerMultiplyRequest,
        _: None = Depends(verify_token),
    ) -> dict[str, Any]:
        from buyer_jobs import run_buyer_multiply

        result = run_buyer_multiply(payload.model_dump())
        deep_job_id = None
        if payload.deep_analyze and result.get("video_path"):
            deep = enqueue(
                "buyer_deep",
                {
                    "video_path": result["video_path"],
                    "analysis_id": result["analysis_id"],
                },
            )
            deep_job_id = deep["job_id"]
        return {
            "status": "completed",
            "analysis_id": result["analysis_id"],
            "analysis": result["analysis"],
            "summary": result["summary"],
            "jobs": job_previews(result.get("jobs") or []),
            "deep_job_id": deep_job_id,
        }
