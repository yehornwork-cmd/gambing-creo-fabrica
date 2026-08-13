#!/usr/bin/env bash
# Hygiene wrapper (MVP P1.3). Not the 500/day scale path.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$ROOT/tools/path_normalizer.py" "$ROOT/library" --recursive
python3 "$ROOT/tools/library_audit.py"
