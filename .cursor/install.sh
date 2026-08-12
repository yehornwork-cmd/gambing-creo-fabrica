#!/usr/bin/env bash
# Idempotent bootstrap for the iGaming Creative Factory bridge repo.
set -euo pipefail

log() { printf '[install] %s\n' "$*"; }

require() {
  local name="$1" bin="$2"
  if ! command -v "$bin" >/dev/null 2>&1; then
    printf '[install] ERROR: required tool "%s" (%s) not found on PATH\n' "$name" "$bin" >&2
    return 1
  fi
  printf '[install] %-8s %s\n' "$name" "$("$bin" --version 2>&1 | head -1)"
}

log "Verifying base toolchain..."
require node node
require npm npm
require python3 python3
require ffmpeg ffmpeg
require git git

CHROME_BIN="$(command -v google-chrome-stable || command -v google-chrome || command -v chromium || true)"
if [[ -n "${CHROME_BIN}" ]]; then
  log "chrome    $("${CHROME_BIN}" --version 2>&1 | head -1) (${CHROME_BIN})"
else
  log "WARNING: no Chrome/Chromium found; HyperFrames headless rendering will be unavailable."
fi

if [[ -f requirements.txt ]]; then
  log "requirements.txt found -> installing Python dependencies"
  python3 -m pip install --user --upgrade --quiet -r requirements.txt
else
  log "No requirements.txt (Python tools use only the standard library)."
fi

if [[ -f package-lock.json ]]; then
  log "package-lock.json found -> npm ci"
  npm ci
elif [[ -f package.json ]]; then
  log "package.json found -> npm install"
  npm install
else
  log "No root package.json (skill scripts run on Node built-ins + node:test)."
fi

log "Environment ready."
