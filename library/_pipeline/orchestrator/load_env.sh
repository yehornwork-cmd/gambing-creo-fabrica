#!/usr/bin/env bash
# Source repo-level env files and gitignored secret keys for factory orchestrators.
# Priority (highest first): runtime secrets → .env → secrets/*.key
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
export REPO_ROOT

SECRETS_DIR="${REPO_ROOT}/library/_pipeline/secrets"

is_placeholder_secret() {
  local val="$1"
  [[ -z "$val" ]] && return 0
  [[ "$val" == YOUR_* ]] && return 0
  [[ "$val" == *"ВСТАВЬ"* ]] && return 0
  return 1
}

# Load KEY=VALUE lines from a dotenv file without overwriting existing runtime secrets.
load_dotenv_file() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%$'\r'}"
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      local var="${BASH_REMATCH[1]}"
      local val="${BASH_REMATCH[2]}"
      # Strip optional surrounding quotes.
      if [[ "$val" =~ ^\"(.*)\"$ ]]; then
        val="${BASH_REMATCH[1]}"
      elif [[ "$val" =~ ^\'(.*)\'$ ]]; then
        val="${BASH_REMATCH[1]}"
      fi
      if [[ -n "${!var:-}" ]]; then
        continue
      fi
      if is_placeholder_secret "$val"; then
        continue
      fi
      export "$var=$val"
    fi
  done < "$file"
}

# Load VAR from secrets/VAR.key when not already exported (runtime secrets win).
load_secret_key() {
  local var="$1"
  if [[ -n "${!var:-}" ]]; then
    return 0
  fi
  local file="${SECRETS_DIR}/${var}.key"
  if [[ -f "$file" ]]; then
    local val
    val="$(tr -d '\n\r' < "$file")"
    if is_placeholder_secret "$val"; then
      return 0
    fi
    export "$var=$val"
  fi
}

load_dotenv_file "${REPO_ROOT}/.env"
load_dotenv_file "${REPO_ROOT}/library/_pipeline/.env"

for secret_var in HF_KEY HF_API_KEY_ID HF_API_KEY_SECRET PERPLEXITY_API_KEY FAL_KEY SPYTREND_CLIENT_ID SPYTREND_CLIENT_SECRET SPYTREND_AUTH_METHOD SPYTREND_API_KEY CAPTURE_API_TOKEN CURSOR_API_KEY; do
  load_secret_key "$secret_var"
done

export PYTHONPATH="${REPO_ROOT}/tools:${PYTHONPATH:-}"
