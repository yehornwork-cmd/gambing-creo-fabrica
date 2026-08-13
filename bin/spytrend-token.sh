#!/usr/bin/env bash
# Mint a fresh SpyTrend MCP Bearer token (headersHelper for Cursor MCP).
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
# shellcheck disable=SC1091
source "${REPO_ROOT}/library/_pipeline/orchestrator/load_env.sh"

: "${SPYTREND_CLIENT_ID:?Missing SPYTREND_CLIENT_ID}"
: "${SPYTREND_CLIENT_SECRET:?Missing SPYTREND_CLIENT_SECRET}"

TOKEN="$(
  curl -sS -u "${SPYTREND_CLIENT_ID}:${SPYTREND_CLIENT_SECRET}" \
    -d 'grant_type=client_credentials' \
    -d 'scope=mcp:read' \
    -d 'audience=https://mcp.spytrend.com/mcp' \
    'https://mcp.spytrend.com/oauth2/token' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
)"

printf '{"Authorization":"Bearer %s"}' "$TOKEN"
