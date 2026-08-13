#!/usr/bin/env bash
# Copy MCP example and ensure SpyTrend OAuth credentials exist.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXAMPLE="${ROOT}/.cursor/mcp.json.example"
TARGET="${ROOT}/.cursor/mcp.json"
SECRETS="${ROOT}/library/_pipeline/secrets"

if [[ ! -f "$EXAMPLE" ]]; then
  echo "Missing ${EXAMPLE}" >&2
  exit 1
fi

if [[ ! -f "$TARGET" ]]; then
  cp "$EXAMPLE" "$TARGET"
  echo "Created ${TARGET} from example."
fi

if [[ ! -f "${SECRETS}/SPYTREND_CLIENT_ID.key" || ! -f "${SECRETS}/SPYTREND_CLIENT_SECRET.key" ]]; then
  echo "Registering SpyTrend OAuth client (free demo tier)..."
  bash "${ROOT}/bin/spytrend-register.sh"
fi

chmod +x "${ROOT}/bin/spytrend-token.sh" "${ROOT}/bin/spytrend-register.sh" 2>/dev/null || true

echo "Enable spytrend + magnific in Cursor Settings → Tools & MCP."
echo "SpyTrend auto-refreshes tokens via bin/spytrend-token.sh."
echo "Magnific uses browser OAuth — reload the server to sign in."
