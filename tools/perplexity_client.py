#!/usr/bin/env python3
"""Perplexity connector — Sonar sync + async deep research via stdlib HTTP."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from media_http import MediaHttpError, request_json

BASE_URL = "https://api.perplexity.ai"
SONAR_URL = f"{BASE_URL}/v1/sonar"
ASYNC_SONAR_URL = f"{BASE_URL}/v1/async/sonar"
DEFAULT_MODEL = "sonar-pro"
DEEP_RESEARCH_MODEL = "sonar-deep-research"
DEFAULT_POLL_INTERVAL = 3.0
DEFAULT_POLL_TIMEOUT = 600.0


def load_api_key() -> str:
    key = os.environ.get("PERPLEXITY_API_KEY", "").strip()
    if not key:
        raise MediaHttpError("Missing PERPLEXITY_API_KEY")
    return key


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {load_api_key()}"}


def sonar_chat(
    messages: list[dict[str, str]],
    *,
    model: str = DEFAULT_MODEL,
    temperature: float | None = None,
    max_tokens: int | None = None,
    **extra: Any,
) -> dict[str, Any]:
    body: dict[str, Any] = {"model": model, "messages": messages}
    if temperature is not None:
        body["temperature"] = temperature
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
    body.update(extra)
    return request_json("POST", SONAR_URL, headers=auth_headers(), body=body)


def async_sonar_submit(
    messages: list[dict[str, str]],
    *,
    model: str = DEEP_RESEARCH_MODEL,
    **extra: Any,
) -> dict[str, Any]:
    request_body: dict[str, Any] = {"model": model, "messages": messages}
    request_body.update(extra)
    return request_json(
        "POST",
        ASYNC_SONAR_URL,
        headers=auth_headers(),
        body={"request": request_body},
    )


def async_sonar_get(api_request_id: str) -> dict[str, Any]:
    return request_json(
        "GET",
        f"{ASYNC_SONAR_URL}/{api_request_id}",
        headers=auth_headers(),
    )


def async_sonar_poll(
    api_request_id: str,
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    poll_timeout: float = DEFAULT_POLL_TIMEOUT,
) -> dict[str, Any]:
    deadline = time.monotonic() + poll_timeout
    while time.monotonic() < deadline:
        current = async_sonar_get(api_request_id)
        state = (current.get("status") or "").lower()
        if state in {"completed", "failed", "cancelled", "canceled"}:
            if state != "completed":
                raise MediaHttpError(f"Async request {api_request_id} ended with status={state}")
            return current
        if current.get("response"):
            return current
        time.sleep(poll_interval)
    raise MediaHttpError(f"Timed out waiting for async request {api_request_id}")


def probe() -> dict[str, Any]:
    """Minimal Sonar call to verify connectivity."""
    result = sonar_chat(
        [{"role": "user", "content": "Reply with exactly: ok"}],
        model="sonar",
        max_tokens=16,
        temperature=0,
    )
    text = ""
    choices = result.get("choices") or []
    if choices:
        text = (choices[0].get("message") or {}).get("content") or ""
    return {"ok": True, "model": result.get("model"), "reply": text.strip()}


def check_auth() -> dict[str, Any]:
    try:
        return probe()
    except MediaHttpError as exc:
        return {"ok": False, "message": str(exc)}


def research(query: str, *, model: str = DEEP_RESEARCH_MODEL, **extra: Any) -> dict[str, Any]:
    submitted = async_sonar_submit([{"role": "user", "content": query}], model=model, **extra)
    api_request_id = submitted.get("id") or submitted.get("request_id")
    if not api_request_id:
        raise MediaHttpError(f"Async submit missing id: {json.dumps(submitted)}")
    return async_sonar_poll(api_request_id)


def enhance(prompt: str, *, context: str | None = None, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    system = (
        "You are a creative director for short-form video ads. "
        "Enhance the user prompt with concrete visual direction, pacing, and CTA hooks. "
        "Return markdown only — no preamble."
    )
    user_parts = [prompt]
    if context:
        user_parts.append(f"\n\nContext:\n{context}")
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n".join(user_parts)},
    ]
    return sonar_chat(messages, model=model, temperature=0.4)


def extract_text(result: dict[str, Any]) -> str:
    if result.get("response"):
        nested = result["response"]
        choices = nested.get("choices") or []
        if choices:
            return (choices[0].get("message") or {}).get("content") or ""
    choices = result.get("choices") or []
    if choices:
        return (choices[0].get("message") or {}).get("content") or ""
    return json.dumps(result, indent=2)


def _read_text(path_or_text: str) -> str:
    path = Path(path_or_text)
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return path_or_text


def cmd_probe(_: argparse.Namespace) -> int:
    print(json.dumps(probe(), indent=2))
    return 0


def cmd_check_auth(_: argparse.Namespace) -> int:
    result = check_auth()
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


def cmd_research(args: argparse.Namespace) -> int:
    query = _read_text(args.query)
    result = research(query, model=args.model)
    print(extract_text(result))
    return 0


def cmd_enhance(args: argparse.Namespace) -> int:
    prompt = _read_text(args.prompt)
    context = _read_text(args.context) if args.context else None
    result = enhance(prompt, context=context, model=args.model)
    print(extract_text(result))
    return 0


def cmd_sonar(args: argparse.Namespace) -> int:
    messages = json.loads(_read_text(args.messages))
    result = sonar_chat(messages, model=args.model, temperature=args.temperature)
    print(json.dumps(result, indent=2))
    return 0


def cmd_async_sonar(args: argparse.Namespace) -> int:
    messages = json.loads(_read_text(args.messages))
    submitted = async_sonar_submit(messages, model=args.model)
    api_request_id = submitted.get("id") or submitted.get("request_id")
    if not api_request_id:
        raise MediaHttpError(f"Missing async id: {json.dumps(submitted)}")
    if args.wait:
        result = async_sonar_poll(api_request_id)
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(submitted, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Perplexity Sonar connector")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("probe", help="Minimal Sonar connectivity check").set_defaults(func=cmd_probe)
    sub.add_parser("check-auth", help="Validate PERPLEXITY_API_KEY").set_defaults(func=cmd_check_auth)

    p_research = sub.add_parser("research", help="Async deep research via /v1/async/sonar")
    p_research.add_argument("query", help="Research question or path to text file")
    p_research.add_argument("--model", default=DEEP_RESEARCH_MODEL)
    p_research.set_defaults(func=cmd_research)

    p_enhance = sub.add_parser("enhance", help="Enhance a creative prompt via sync Sonar")
    p_enhance.add_argument("prompt", help="Prompt text or path to markdown file")
    p_enhance.add_argument("--context", default=None, help="Optional context file")
    p_enhance.add_argument("--model", default=DEFAULT_MODEL)
    p_enhance.set_defaults(func=cmd_enhance)

    p_sonar = sub.add_parser("sonar", help="Sync chat completion at /v1/sonar")
    p_sonar.add_argument("messages", help='JSON messages array or path e.g. \'[{"role":"user","content":"hi"}]\'')
    p_sonar.add_argument("--model", default=DEFAULT_MODEL)
    p_sonar.add_argument("--temperature", type=float, default=None)
    p_sonar.set_defaults(func=cmd_sonar)

    p_async = sub.add_parser("async-sonar", help="Submit async Sonar job")
    p_async.add_argument("messages", help="JSON messages array or path")
    p_async.add_argument("--model", default=DEEP_RESEARCH_MODEL)
    p_async.add_argument("--wait", action="store_true", help="Poll until completion")
    p_async.set_defaults(func=cmd_async_sonar)

    args = parser.parse_args()
    try:
        return args.func(args)
    except MediaHttpError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
