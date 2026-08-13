#!/usr/bin/env python3
"""Install isolated-project renderer on the live host and raise CONCURRENCY."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "server.mjs"
LIVE = Path("/opt/forge/src/app/app/renderer/server.mjs")
COMPOSE = Path("/opt/forge/renderer-compose.yml")
CONTAINER = "forge-forge-renderer-1"
TARGET_CONCURRENCY = 4


def main() -> int:
    if not SRC.is_file():
        print(f"error: {SRC} missing", file=sys.stderr)
        return 2
    LIVE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC, LIVE)
    print(f"copied {SRC} → {LIVE}")

    if COMPOSE.is_file():
        text = COMPOSE.read_text(encoding="utf-8")
        next_text, n = re.subn(
            r'CONCURRENCY:\s*"\d+"',
            f'CONCURRENCY: "{TARGET_CONCURRENCY}"',
            text,
            count=1,
        )
        if n:
            COMPOSE.write_text(next_text, encoding="utf-8")
            print(f"compose CONCURRENCY={TARGET_CONCURRENCY}")
        else:
            print("compose CONCURRENCY line not found — skipped")

    subprocess.check_call(["docker", "cp", str(LIVE), f"{CONTAINER}:/srv/server.mjs"])
    subprocess.check_call(["docker", "restart", CONTAINER])
    print(f"restarted {CONTAINER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
