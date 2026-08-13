#!/usr/bin/env bash
# Source repo-level env files and gitignored secret keys for factory orchestrators.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
export REPO_ROOT

SECRETS_DIR="${REPO_ROOT}/library/_pipeline/secrets"

# Load VAR from secrets/VAR.key when not already exported (runtime secrets win).
load_secret_key() {
  local var="$1"
  if [[ -n "${!var:-}" ]]; then
    return 0
  fi
  local file="${SECRETS_DIR}/${var}.key"
  if [[ -f "$file" ]]; then
    # shellcheck disable=SC2163
    export "$var=$(tr -d '\n\r' < "$file")"
  fi
}

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

for secret_var in HF_KEY HF_API_KEY_ID HF_API_KEY_SECRET PERPLEXITY_API_KEY FAL_KEY SPYTREND_API_KEY CAPTURE_API_TOKEN CURSOR_API_KEY; do
  load_secret_key "$secret_var"
done

export PYTHONPATH="${REPO_ROOT}/tools:${PYTHONPATH:-}"
