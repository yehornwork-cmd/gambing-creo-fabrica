#!/usr/bin/env python3
"""Gemini native-video helper for buyer deep analysis.

Reads GEMINI_API_KEY or secrets/gemini.key (one line). Short clips use inline
base64; longer masters go through the Gemini File API. Failures return None
so the heuristic beat map stays in place.
"""

from __future__ import annotations

import json
import os
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    import certifi

    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:  # pragma: no cover
    SSL_CTX = ssl.create_default_context()

PIPELINE_ROOT = Path(__file__).resolve().parent.parent
KEY_FILE = PIPELINE_ROOT / "secrets" / "gemini.key"
GEMINI_VISION_MODEL = os.environ.get("GEMINI_VISION_MODEL", "gemini-2.5-flash")
INLINE_LIMIT = 18 * 1024 * 1024


def load_gemini_api_key() -> str:
    env = os.environ.get("GEMINI_API_KEY", "").strip()
    if env:
        return env
    if not KEY_FILE.exists():
        return ""
    for line in KEY_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        return line
    return ""


def _http_json(req: urllib.request.Request, *, timeout: float) -> dict[str, Any]:
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
        raw = resp.read().decode("utf-8")
    if not raw:
        return {}
    return json.loads(raw)


def upload_video(path: Path, api_key: str, *, timeout: float = 120) -> str | None:
    """Return a file_uri or None."""
    size = path.stat().st_size
    start = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={api_key}",
        data=json.dumps({"file": {"display_name": path.name}}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(size),
            "X-Goog-Upload-Header-Content-Type": "video/mp4",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(start, timeout=timeout, context=SSL_CTX) as resp:
            upload_url = resp.headers.get("X-Goog-Upload-URL") or resp.headers.get("x-goog-upload-url")
    except urllib.error.HTTPError:
        return None
    if not upload_url:
        return None
    body = path.read_bytes()
    finish = urllib.request.Request(
        upload_url,
        data=body,
        headers={
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Command": "upload, finalize",
            "Content-Length": str(len(body)),
        },
        method="POST",
    )
    try:
        payload = _http_json(finish, timeout=timeout)
    except urllib.error.HTTPError:
        return None
    return (payload.get("file") or {}).get("uri")


def generate_json(
    *,
    api_key: str,
    prompt: str,
    video: Path,
    timeout: float = 120,
) -> dict[str, Any] | None:
    size = video.stat().st_size
    parts: list[dict[str, Any]]
    if size <= INLINE_LIMIT:
        import base64

        parts = [
            {
                "inline_data": {
                    "mime_type": "video/mp4",
                    "data": base64.standard_b64encode(video.read_bytes()).decode("ascii"),
                }
            },
            {"text": prompt},
        ]
    else:
        uri = upload_video(video, api_key, timeout=timeout)
        if not uri:
            return None
        # Files can take a moment to become ACTIVE.
        time.sleep(1.5)
        parts = [
            {"file_data": {"mime_type": "video/mp4", "file_uri": uri}},
            {"text": prompt},
        ]
    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_VISION_MODEL}:generateContent?key={api_key}"
    )
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        payload = _http_json(req, timeout=timeout)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    candidates = payload.get("candidates") or []
    if not candidates:
        return None
    text = ""
    for part in ((candidates[0].get("content") or {}).get("parts") or []):
        text += str(part.get("text") or "")
    text = text.strip()
    if not text:
        return None
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else {"beats": parsed}
