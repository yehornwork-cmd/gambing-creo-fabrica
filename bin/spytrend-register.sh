#!/usr/bin/env bash
# Self-register a SpyTrend OAuth client (free demo tier) and save gitignored keys.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
SECRETS="${REPO_ROOT}/library/_pipeline/secrets"
NAME="${1:-gambing-creo-fabrica-agent}"

mkdir -p "$SECRETS"

RESP="$(curl -sS -X POST 'https://mcp.spytrend.com/oauth2/register' \
  -H 'Content-Type: application/json' \
  -d "{\"client_name\":\"${NAME}\",\"grant_types\":[\"client_credentials\"],\"response_types\":[],\"token_endpoint_auth_method\":\"client_secret_basic\",\"scope\":\"mcp:read\"}")"

CLIENT_ID="$(printf '%s' "$RESP" | python3 -c 'import json,sys; print(json.load(sys.stdin)["client_id"])')"
CLIENT_SECRET="$(printf '%s' "$RESP" | python3 -c 'import json,sys; print(json.load(sys.stdin)["client_secret"])')"

printf '%s' "$CLIENT_ID" > "${SECRETS}/SPYTREND_CLIENT_ID.key"
printf '%s' "$CLIENT_SECRET" > "${SECRETS}/SPYTREND_CLIENT_SECRET.key"
printf '%s' "basic" > "${SECRETS}/SPYTREND_AUTH_METHOD.key"
chmod 600 "${SECRETS}/SPYTREND_CLIENT_ID.key" "${SECRETS}/SPYTREND_CLIENT_SECRET.key" "${SECRETS}/SPYTREND_AUTH_METHOD.key"

echo "Saved SpyTrend OAuth credentials to library/_pipeline/secrets/"
echo "client_id: ${CLIENT_ID}"
echo "Run: bin/spytrend-token.sh"
