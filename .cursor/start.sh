#!/usr/bin/env bash
# Per-boot factory connector wiring (non-fatal when keys are absent).
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
chmod +x "${REPO_ROOT}/bin/connect-factory" 2>/dev/null || true

if [[ -x "${REPO_ROOT}/bin/connect-factory" ]]; then
  "${REPO_ROOT}/bin/connect-factory" || true
fi

# Background marathon daemon when enabled (polls for media keys, runs batch + live execute).
if [[ "${FACTORY_MARATHON_DAEMON:-}" == "1" && -x "${REPO_ROOT}/bin/marathon-daemon" ]]; then
  if ! pgrep -f "bin/marathon-daemon" >/dev/null 2>&1; then
    nohup "${REPO_ROOT}/bin/marathon-daemon" >>"${REPO_ROOT}/library/_pipeline/runs/marathon_daemon.log" 2>&1 &
  fi
fi
