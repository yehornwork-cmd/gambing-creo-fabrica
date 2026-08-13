#!/usr/bin/env python3
"""fal.ai queue API client — stdlib HTTP via media_http."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from media_http import MediaHttpError, request_json

BASE_URL = "https://queue.fal.run"
DEFAULT_POLL_INTERVAL = 2.0
DEFAULT_POLL_TIMEOUT = 300.0
TERMINAL_STATUSES = {"COMPLETED", "FAILED", "CANCELED", "CANCELLED"}


def load_fal_key() -> str:
    key = os.environ.get("FAL_KEY", "").strip()
    if not key:
        raise MediaHttpError("Missing FAL_KEY")
    return key


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Key {load_fal_key()}"}


def model_url(model_id: str) -> str:
    model_id = model_id.lstrip("/")
    return f"{BASE_URL}/{model_id}"


def submit(model_id: str, arguments: dict[str, Any], *, webhook_url: str | None = None) -> dict[str, Any]:
    url = model_url(model_id)
    if webhook_url:
        url = f"{url}?fal_webhook={webhook_url}"
    return request_json("POST", url, headers=auth_headers(), body=arguments)


def status(model_id: str, request_id: str, *, with_logs: bool = False) -> dict[str, Any]:
    url = f"{model_url(model_id)}/requests/{request_id}/status"
    if with_logs:
        url = f"{url}?logs=1"
    return request_json("GET", url, headers=auth_headers())


def result(model_id: str, request_id: str) -> dict[str, Any]:
    return request_json("GET", f"{model_url(model_id)}/requests/{request_id}", headers=auth_headers())


def subscribe(
    model_id: str,
    arguments: dict[str, Any],
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    poll_timeout: float = DEFAULT_POLL_TIMEOUT,
    webhook_url: str | None = None,
    with_logs: bool = False,
) -> dict[str, Any]:
    queued = submit(model_id, arguments, webhook_url=webhook_url)
    request_id = queued.get("request_id")
    if not request_id:
        raise MediaHttpError(f"Submit response missing request_id: {json.dumps(queued)}")

    deadline = time.monotonic() + poll_timeout
    while time.monotonic() < deadline:
        current = status(model_id, request_id, with_logs=with_logs)
        state = current.get("status", "")
        if state in TERMINAL_STATUSES:
            if state != "COMPLETED":
                raise MediaHttpError(f"Request {request_id} ended with status={state}: {json.dumps(current)}")
            return result(model_id, request_id)
        time.sleep(poll_interval)

    raise MediaHttpError(f"Timed out waiting for request {request_id} after {poll_timeout}s")


def check_auth() -> dict[str, Any]:
    """Validate FAL_KEY by hitting a lightweight model metadata endpoint."""
    try:
        # Status on a bogus id still authenticates; 404 means auth worked.
        request_json("GET", f"{BASE_URL}/fal-ai/flux/schnell/requests/00000000-0000-0000-0000-000000000000/status", headers=auth_headers())
        return {"ok": True, "message": "Unexpected success on probe request"}
    except MediaHttpError as exc:
        message = str(exc)
        if "HTTP 401" in message or "HTTP 403" in message:
            return {"ok": False, "message": message}
        if "HTTP 404" in message or "HTTP 422" in message:
            return {"ok": True, "message": "FAL_KEY accepted"}
        return {"ok": False, "message": message}


def _load_json_arg(value: str) -> dict[str, Any]:
    path = Path(value)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(value)


def cmd_submit(args: argparse.Namespace) -> int:
    payload = _load_json_arg(args.arguments)
    out = submit(args.model_id, payload, webhook_url=args.webhook_url)
    print(json.dumps(out, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    out = status(args.model_id, args.request_id, with_logs=args.logs)
    print(json.dumps(out, indent=2))
    return 0


def cmd_subscribe(args: argparse.Namespace) -> int:
    payload = _load_json_arg(args.arguments)
    out = subscribe(
        args.model_id,
        payload,
        poll_interval=args.poll_interval,
        poll_timeout=args.poll_timeout,
        webhook_url=args.webhook_url,
        with_logs=args.logs,
    )
    print(json.dumps(out, indent=2))
    return 0


def cmd_check_auth(_: argparse.Namespace) -> int:
    out = check_auth()
    print(json.dumps(out, indent=2))
    return 0 if out.get("ok") else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="fal.ai queue API client")
    sub = parser.add_subparsers(dest="command", required=True)

    p_submit = sub.add_parser("submit", help="Queue a model inference request")
    p_submit.add_argument("model_id", help="Model id e.g. fal-ai/flux/schnell")
    p_submit.add_argument("arguments", help="JSON body or path to JSON file")
    p_submit.add_argument("--webhook-url", default=None)
    p_submit.set_defaults(func=cmd_submit)

    p_status = sub.add_parser("status", help="Poll queued request status")
    p_status.add_argument("model_id")
    p_status.add_argument("request_id")
    p_status.add_argument("--logs", action="store_true")
    p_status.set_defaults(func=cmd_status)

    p_sub = sub.add_parser("subscribe", help="Submit and poll until result is ready")
    p_sub.add_argument("model_id")
    p_sub.add_argument("arguments", help="JSON body or path to JSON file")
    p_sub.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL)
    p_sub.add_argument("--poll-timeout", type=float, default=DEFAULT_POLL_TIMEOUT)
    p_sub.add_argument("--webhook-url", default=None)
    p_sub.add_argument("--logs", action="store_true")
    p_sub.set_defaults(func=cmd_subscribe)

    p_auth = sub.add_parser("check-auth", help="Validate FAL_KEY")
    p_auth.set_defaults(func=cmd_check_auth)

    args = parser.parse_args()
    try:
        return args.func(args)
    except MediaHttpError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
