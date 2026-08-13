"""Shared HTTP helpers for factory media connectors."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Any

try:
    import certifi

    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()

DEFAULT_USER_AGENT = "nanobanana-factory/1.0 media-connector"


class MediaHttpError(RuntimeError):
    pass


def request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    timeout: float = 120.0,
) -> Any:
    req_headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"}
    if headers:
        req_headers.update(headers)

    payload: bytes | None = None
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=payload, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
            raw = response.read()
            if not raw:
                return None
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise MediaHttpError(f"HTTP {exc.code} {method} {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise MediaHttpError(f"Network error {method} {url}: {exc}") from exc


def request_bytes(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    timeout: float = 120.0,
) -> tuple[int, bytes]:
    req_headers = {"User-Agent": DEFAULT_USER_AGENT}
    if headers:
        req_headers.update(headers)

    request = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise MediaHttpError(f"HTTP {exc.code} {method} {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise MediaHttpError(f"Network error {method} {url}: {exc}") from exc
