#!/usr/bin/env python3
"""Give Factory v3 room to finish a multi-geo render wave.

N8N_RUNNERS_TASK_TIMEOUT=300 killed the Code node once 4 Chromium jobs
ran together (~5 min). Buyer batches of 4–8 geos need a longer slot.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

COMPOSE = Path("/opt/video-factory/docker-compose.yml")
TARGET = 900


def main() -> int:
    text = COMPOSE.read_text(encoding="utf-8")
    next_text, n = re.subn(
        r"N8N_RUNNERS_TASK_TIMEOUT:\s*\d+",
        f"N8N_RUNNERS_TASK_TIMEOUT: {TARGET}",
        text,
        count=1,
    )
    if n == 0:
        print("timeout line not found", file=sys.stderr)
        return 2
    if next_text == text:
        print(f"already {TARGET}")
        return 0
    COMPOSE.write_text(next_text, encoding="utf-8")
    print(f"set N8N_RUNNERS_TASK_TIMEOUT={TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
