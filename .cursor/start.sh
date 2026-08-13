#!/usr/bin/env bash
# Per-boot factory connector wiring (non-fatal when keys are absent).
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
chmod +x "${REPO_ROOT}/bin/connect-factory" 2>/dev/null || true

if [[ -x "${REPO_ROOT}/bin/connect-factory" ]]; then
  "${REPO_ROOT}/bin/connect-factory" || true
fi
