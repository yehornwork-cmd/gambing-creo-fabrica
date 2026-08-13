#!/usr/bin/env python3
"""Poll connector auth until all pass or timeout (for unattended marathon sessions)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONNECT = REPO_ROOT / "bin" / "connect-factory"


def check_strict() -> bool:
    proc = subprocess.run(
        ["bash", str(CONNECT), "--strict"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return proc.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Wait for all factory connectors to authenticate")
    parser.add_argument("--interval", type=float, default=60.0)
    parser.add_argument("--timeout", type=float, default=21600.0, help="Default 6 hours")
    args = parser.parse_args()

    deadline = time.monotonic() + args.timeout
    attempt = 0
    while time.monotonic() < deadline:
        attempt += 1
        if check_strict():
            print(json.dumps({"ok": True, "attempts": attempt}, indent=2))
            return 0
        time.sleep(args.interval)

    print(json.dumps({"ok": False, "attempts": attempt, "message": "timeout"}, indent=2), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
