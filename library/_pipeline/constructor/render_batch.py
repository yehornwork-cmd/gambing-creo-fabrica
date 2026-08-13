#!/usr/bin/env python3
"""F1.1: render constructor batch.json through HyperFrames --batch.

Requires Node >= 22 and `npx hyperframes`. Placeholder plates live in
output/gates-pilot-ad-v3/frames/. MP4s are written to output/renders/ (gitignored).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PROJECT = REPO / "output" / "gates-pilot-ad-v3"
BATCH = REPO / "library" / "_pipeline" / "constructor" / "jobs" / "batch.json"
OUT_DIR = REPO / "output" / "renders"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=Path, default=BATCH)
    parser.add_argument("--project", type=Path, default=PROJECT)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--quality", default="draft", choices=["draft", "high"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if shutil.which("npx") is None:
        print("error: npx not on PATH", file=sys.stderr)
        return 2
    node = subprocess.run(["node", "-v"], capture_output=True, text=True)
    ver = (node.stdout or "").strip().lstrip("v")
    major = int(ver.split(".", 1)[0]) if ver else 0
    if major < 22:
        print(f"error: HyperFrames needs Node >= 22 (have {ver or 'unknown'})", file=sys.stderr)
        return 2
    if not args.batch.is_file():
        print(f"error: batch not found: {args.batch}", file=sys.stderr)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "npx",
        "--yes",
        "hyperframes",
        "render",
        str(args.project),
        "--batch",
        str(args.batch),
        "--output",
        str(args.out_dir / "{name}.mp4"),
        "--quality",
        args.quality,
        "--batch-concurrency",
        "1",
        "--strict-variables",
        "--json",
    ]
    print(" ".join(cmd))
    if args.dry_run:
        return 0
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
