#!/usr/bin/env python3
"""Idempotent patches for youtube-worker: buyer multiply routes."""

from __future__ import annotations

from pathlib import Path

DEPLOY = Path(__file__).resolve().parent
WORKER = DEPLOY / "remote_worker.py"
RUNNER = DEPLOY / "youtube_job_runner.py"

WORKER_IMPORT = """
try:
    import buyer_routes

    buyer_routes.register(app, verify_token=_verify_token, enqueue=_enqueue)
except Exception as exc:  # pragma: no cover - worker still serves VOD jobs
    print(f"buyer_routes not loaded: {exc}", flush=True)
"""

RUNNER_BRANCH = '''    if job_type == "buyer_deep":
        from buyer_jobs import run_buyer_deep

        return run_buyer_deep(params)
    if job_type == "buyer_multiply":
        from buyer_jobs import run_buyer_multiply

        return run_buyer_multiply(params)
'''


def patch_worker() -> None:
    text = WORKER.read_text(encoding="utf-8")
    if '"buyer_multiply"' not in text:
        old = '"capture_enabled": False,\n    }'
        new = '"capture_enabled": False,\n        "buyer_multiply": True,\n    }'
        if old not in text:
            raise SystemExit("health() capture_enabled marker missing")
        text = text.replace(old, new, 1)
    if "buyer_routes" not in text:
        marker = '    return {"jobs": jobs, "count": len(jobs)}\n'
        if marker not in text:
            raise SystemExit("list_jobs return marker missing")
        text = text.replace(marker, marker + "\n" + WORKER_IMPORT + "\n", 1)
    WORKER.write_text(text, encoding="utf-8")


def patch_runner() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    if 'job_type == "buyer_deep"' in text:
        return
    old = '    raise ValueError(f"Unknown job_type: {job_type}")\n'
    if old not in text:
        raise SystemExit("runner raise marker missing")
    RUNNER.write_text(text.replace(old, RUNNER_BRANCH + old, 1), encoding="utf-8")


def main() -> int:
    patch_worker()
    patch_runner()
    print(f"patched {WORKER}")
    print(f"patched {RUNNER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
