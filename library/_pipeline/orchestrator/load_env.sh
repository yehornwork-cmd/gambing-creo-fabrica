#!/usr/bin/env bash
# Source repo-level and pipeline-level env files for factory orchestrators.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
export REPO_ROOT

set -a
if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/.env"
fi
if [[ -f "${REPO_ROOT}/library/_pipeline/.env" ]]; then
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/library/_pipeline/.env"
fi
set +a

export PYTHONPATH="${REPO_ROOT}/tools:${PYTHONPATH:-}"
