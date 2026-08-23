#!/usr/bin/env bash
# Idempotent bootstrap for the iGaming Creative Factory bridge repo.
#
# This repository is a "bridge repo": `main` is intentionally minimal and the
# real work (Game DNA, HyperFrames video tooling, helper scripts) lands on
# `cursor/*` branches. The default Cloud Agent image already ships the full
# toolchain this repo relies on (Node.js, Python 3, ffmpeg, Google Chrome), so
# this script only:
#   1. verifies that toolchain is present and prints versions, and
#   2. installs per-branch dependencies *when* a branch actually ships a
#      manifest (requirements.txt / package.json).
#
# It is safe to run repeatedly and on branches that carry no manifests
# (including main), which keeps a single committed environment usable across
# every branch of the repo.
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

# Chrome (used by HyperFrames rendering via puppeteer-core / headless capture).
CHROME_BIN="$(command -v google-chrome-stable || command -v google-chrome || command -v chromium || true)"
if [[ -n "${CHROME_BIN}" ]]; then
  log "chrome    $("${CHROME_BIN}" --version 2>&1 | head -1) (${CHROME_BIN})"
else
  log "WARNING: no Chrome/Chromium found; HyperFrames headless rendering will be unavailable."
fi

# Per-branch Python dependencies (guarded: most branches ship none).
if [[ -f requirements.txt ]]; then
  log "requirements.txt found -> installing Python dependencies"
  python3 -m pip install --user --upgrade --quiet -r requirements.txt
else
  log "No requirements.txt (Python tools use only the standard library)."
fi

# Per-branch Node dependencies (guarded: skill scripts use Node built-ins).
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
