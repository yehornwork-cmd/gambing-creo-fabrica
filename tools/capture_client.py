#!/usr/bin/env python3
"""Hetzner capture worker client — submit and poll gameplay capture jobs."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from media_http import MediaHttpError, request_json

DEFAULT_WORKER_URL = "http://127.0.0.1:8787"


def load_token() -> str:
    token = os.environ.get("CAPTURE_API_TOKEN", "").strip()
    if not token:
        raise MediaHttpError("Missing CAPTURE_API_TOKEN")
    return token


def worker_url() -> str:
    return os.environ.get("CAPTURE_WORKER_URL", DEFAULT_WORKER_URL).rstrip("/")


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {load_token()}"}


def submit_capture(
    game_id: str,
    *,
    spins: int = 80,
    profile: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"game_id": game_id, "spins": spins}
    if profile:
        body["profile"] = profile
    return request_json(
        "POST",
        f"{worker_url()}/jobs/capture",
        headers=auth_headers(),
        body=body,
        timeout=30.0,
    )


def job_status(job_id: str) -> dict[str, Any]:
    return request_json(
        "GET",
        f"{worker_url()}/jobs/{job_id}",
        headers=auth_headers(),
        timeout=30.0,
    )


def wait_for_job(
    job_id: str,
    *,
    poll_interval: float = 5.0,
    poll_timeout: float = 3600.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + poll_timeout
    while time.monotonic() < deadline:
        current = job_status(job_id)
        state = (current.get("status") or current.get("state") or "").lower()
        if state in {"completed", "done", "success", "succeeded"}:
            return current
        if state in {"failed", "error", "canceled", "cancelled"}:
            raise MediaHttpError(f"Capture job {job_id} ended with status={state}: {json.dumps(current)}")
        time.sleep(poll_interval)
    raise MediaHttpError(f"Timed out waiting for capture job {job_id}")


def check_auth() -> dict[str, Any]:
    """Probe worker health; 401 means bad token, connection error means unreachable."""
    try:
        request_json("GET", f"{worker_url()}/health", headers=auth_headers(), timeout=10.0)
        return {"ok": True, "message": "Capture worker reachable", "url": worker_url()}
    except MediaHttpError as exc:
        message = str(exc)
        if "HTTP 401" in message or "HTTP 403" in message:
            return {"ok": False, "message": message, "url": worker_url()}
        if "HTTP 404" in message:
            return {"ok": True, "message": "Worker reachable (no /health endpoint)", "url": worker_url()}
        return {"ok": False, "message": message, "url": worker_url()}


def cmd_submit(args: argparse.Namespace) -> int:
    out = submit_capture(args.game_id, spins=args.spins, profile=args.profile)
    print(json.dumps(out, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    out = job_status(args.job_id)
    print(json.dumps(out, indent=2))
    return 0


def cmd_wait(args: argparse.Namespace) -> int:
    out = wait_for_job(args.job_id, poll_interval=args.poll_interval, poll_timeout=args.poll_timeout)
    print(json.dumps(out, indent=2))
    return 0


def cmd_check_auth(_: argparse.Namespace) -> int:
    out = check_auth()
    print(json.dumps(out, indent=2))
    return 0 if out.get("ok") else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Gameplay capture worker client")
    sub = parser.add_subparsers(dest="command", required=True)

    p_submit = sub.add_parser("submit", help="Queue a capture job")
    p_submit.add_argument("game_id", help="Game id e.g. vs20olympgate")
    p_submit.add_argument("--spins", type=int, default=80)
    p_submit.add_argument("--profile", default=None)
    p_submit.set_defaults(func=cmd_submit)

    p_status = sub.add_parser("status", help="Poll capture job status")
    p_status.add_argument("job_id")
    p_status.set_defaults(func=cmd_status)

    p_wait = sub.add_parser("wait", help="Poll until capture job completes")
    p_wait.add_argument("job_id")
    p_wait.add_argument("--poll-interval", type=float, default=5.0)
    p_wait.add_argument("--poll-timeout", type=float, default=3600.0)
    p_wait.set_defaults(func=cmd_wait)

    sub.add_parser("check-auth", help="Validate CAPTURE_API_TOKEN and worker URL").set_defaults(
        func=cmd_check_auth
    )

    args = parser.parse_args()
    try:
        return args.func(args)
    except MediaHttpError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
