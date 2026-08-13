#!/usr/bin/env python3
"""Higgsfield platform API client — stdlib HTTP via media_http."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
from pathlib import Path
from typing import Any

from media_http import MediaHttpError, request_bytes, request_json

BASE_URL = "https://platform.higgsfield.ai"
DEFAULT_POLL_INTERVAL = 2.0
DEFAULT_POLL_TIMEOUT = 300.0
TERMINAL_STATUSES = {"completed", "failed", "nsfw", "canceled"}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_hf_credentials() -> str:
    """Return KEY_ID:KEY_SECRET from HF_KEY or split env vars."""
    combined = os.environ.get("HF_KEY", "").strip()
    if combined:
        return combined

    key_id = os.environ.get("HF_API_KEY_ID", "").strip()
    key_secret = os.environ.get("HF_API_KEY_SECRET", "").strip()
    if key_id and key_secret:
        return f"{key_id}:{key_secret}"

    raise MediaHttpError(
        "Missing Higgsfield credentials. Set HF_KEY or HF_API_KEY_ID + HF_API_KEY_SECRET."
    )


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Key {load_hf_credentials()}"}


def endpoint_url(endpoint: str) -> str:
    endpoint = endpoint.lstrip("/")
    return f"{BASE_URL}/{endpoint}"


def submit(endpoint: str, arguments: dict[str, Any], *, webhook_url: str | None = None) -> dict[str, Any]:
    body = dict(arguments)
    if webhook_url:
        body["webhook_url"] = webhook_url
    return request_json("POST", endpoint_url(endpoint), headers=auth_headers(), body=body)


def status(request_id: str) -> dict[str, Any]:
    return request_json(
        "GET",
        f"{BASE_URL}/requests/{request_id}/status",
        headers=auth_headers(),
    )


def cancel(request_id: str) -> None:
    request_json("POST", f"{BASE_URL}/requests/{request_id}/cancel", headers=auth_headers())


def subscribe(
    endpoint: str,
    arguments: dict[str, Any],
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    poll_timeout: float = DEFAULT_POLL_TIMEOUT,
    webhook_url: str | None = None,
) -> dict[str, Any]:
    queued = submit(endpoint, arguments, webhook_url=webhook_url)
    request_id = queued.get("request_id")
    if not request_id:
        raise MediaHttpError(f"Submit response missing request_id: {json.dumps(queued)}")

    deadline = time.monotonic() + poll_timeout
    while time.monotonic() < deadline:
        current = status(request_id)
        state = current.get("status", "")
        if state in TERMINAL_STATUSES:
            if state != "completed":
                detail = current.get("error") or state
                raise MediaHttpError(f"Request {request_id} ended with status={state}: {detail}")
            return current
        time.sleep(poll_interval)

    raise MediaHttpError(f"Timed out waiting for request {request_id} after {poll_timeout}s")


def generate_upload_url(content_type: str) -> dict[str, Any]:
    return request_json(
        "POST",
        f"{BASE_URL}/files/generate-upload-url",
        headers=auth_headers(),
        body={"content_type": content_type},
    )


def upload_file(path: Path, *, content_type: str | None = None) -> str:
    if not path.is_file():
        raise MediaHttpError(f"Upload file not found: {path}")

    guessed = content_type or mimetypes.guess_type(path.name)[0]
    if not guessed:
        raise MediaHttpError(f"Could not infer content_type for {path}; pass --content-type")

    presign = generate_upload_url(guessed)
    upload_url = presign.get("upload_url")
    public_url = presign.get("public_url")
    upload_headers = presign.get("upload_headers") or {}

    if not upload_url or not public_url:
        raise MediaHttpError(f"Unexpected upload response: {json.dumps(presign)}")

    headers = {str(k): str(v) for k, v in upload_headers.items()}
    request_bytes("PUT", upload_url, headers=headers, body=path.read_bytes(), timeout=300.0)
    return public_url


def check_auth() -> dict[str, Any]:
    """Validate credentials by requesting an upload URL (lightweight authenticated call)."""
    try:
        result = generate_upload_url("image/jpeg")
        return {"ok": True, "message": "Higgsfield credentials accepted", "sample": result.get("public_url")}
    except MediaHttpError as exc:
        return {"ok": False, "message": str(exc)}


def _load_json_arg(value: str) -> dict[str, Any]:
    path = Path(value)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(value)


def cmd_submit(args: argparse.Namespace) -> int:
    payload = _load_json_arg(args.arguments)
    result = submit(args.endpoint, payload, webhook_url=args.webhook_url)
    print(json.dumps(result, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    result = status(args.request_id)
    print(json.dumps(result, indent=2))
    return 0


def cmd_subscribe(args: argparse.Namespace) -> int:
    payload = _load_json_arg(args.arguments)
    result = subscribe(
        args.endpoint,
        payload,
        poll_interval=args.poll_interval,
        poll_timeout=args.poll_timeout,
        webhook_url=args.webhook_url,
    )
    print(json.dumps(result, indent=2))
    return 0


def cmd_upload(args: argparse.Namespace) -> int:
    public_url = upload_file(Path(args.file), content_type=args.content_type)
    print(json.dumps({"public_url": public_url}, indent=2))
    return 0


def cmd_check_auth(_: argparse.Namespace) -> int:
    result = check_auth()
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Higgsfield platform API client")
    sub = parser.add_subparsers(dest="command", required=True)

    p_submit = sub.add_parser("submit", help="Submit a generation request")
    p_submit.add_argument("endpoint", help="Model endpoint e.g. higgsfield-ai/soul/standard")
    p_submit.add_argument("arguments", help="JSON body or path to JSON file")
    p_submit.add_argument("--webhook-url", default=None)
    p_submit.set_defaults(func=cmd_submit)

    p_status = sub.add_parser("status", help="Poll request status")
    p_status.add_argument("request_id")
    p_status.set_defaults(func=cmd_status)

    p_sub = sub.add_parser("subscribe", help="Submit and poll until completion")
    p_sub.add_argument("endpoint")
    p_sub.add_argument("arguments", help="JSON body or path to JSON file")
    p_sub.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL)
    p_sub.add_argument("--poll-timeout", type=float, default=DEFAULT_POLL_TIMEOUT)
    p_sub.add_argument("--webhook-url", default=None)
    p_sub.set_defaults(func=cmd_subscribe)

    p_upload = sub.add_parser("upload", help="Upload a local file and return public_url")
    p_upload.add_argument("file")
    p_upload.add_argument("--content-type", default=None)
    p_upload.set_defaults(func=cmd_upload)

    p_auth = sub.add_parser("check-auth", help="Validate HF_KEY credentials")
    p_auth.set_defaults(func=cmd_check_auth)

    args = parser.parse_args()
    try:
        return args.func(args)
    except MediaHttpError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
