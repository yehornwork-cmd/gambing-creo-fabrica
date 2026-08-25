#!/usr/bin/env bash
# Idempotent bootstrap for the iGaming Creative Factory bridge repo.
#
# This repository is a "bridge repo": `main` is intentionally minimal and the
# real work lands on `cursor/*` branches:
#   * a pure-stdlib Python orchestrator
#     (`library/_pipeline/orchestrator/factory_run.py`), and
#   * Node.js media/creative "HyperFrames" skill scripts under
#     `context/hf-skills/**` that run on Node built-ins + the `node:test`
#     runner (no root package.json / requirements.txt).
#
# The default Cloud Agent image already ships the full toolchain this repo
# relies on (Node.js, npm, Python 3, ffmpeg, git, Google Chrome), so this
# script only:
#   1. verifies that toolchain is present and prints versions, and
#   2. installs per-branch dependencies *when* a branch actually ships a
#      manifest (requirements.txt / package.json), including nested subproject
#      manifests such as the Remotion test corpora.
#
# It is safe to run repeatedly and on branches that carry no manifests
# (including `main`), which keeps a single committed environment usable across
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

# Chrome is used by the HyperFrames rendering/capture flows (headless Chrome
# via puppeteer-core). It ships in the default image; warn rather than fail so
# non-rendering branches still install cleanly.
CHROME_BIN="$(command -v google-chrome-stable || command -v google-chrome || command -v chromium || command -v chromium-browser || true)"
if [[ -n "${CHROME_BIN}" ]]; then
  log "chrome   $("${CHROME_BIN}" --version 2>&1 | head -1) (${CHROME_BIN})"
else
  log "WARNING: no Chrome/Chromium found; HyperFrames headless rendering will be unavailable."
fi

# Root-level Python dependencies (guarded: most branches ship none — the
# orchestrator and helper tools use only the standard library).
if [[ -f requirements.txt ]]; then
  log "requirements.txt found -> installing Python dependencies"
  python3 -m pip install --user --upgrade --quiet -r requirements.txt
else
  log "No root requirements.txt (Python tools use only the standard library)."
fi

# Root-level Node dependencies (guarded: skill scripts run on Node built-ins
# and the node:test runner, so most branches ship no root manifest).
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
