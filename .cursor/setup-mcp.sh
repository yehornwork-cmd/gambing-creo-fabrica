#!/usr/bin/env bash
# Copy MCP example into gitignored mcp.json when missing.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXAMPLE="${ROOT}/.cursor/mcp.json.example"
TARGET="${ROOT}/.cursor/mcp.json"

if [[ ! -f "$EXAMPLE" ]]; then
  echo "Missing ${EXAMPLE}" >&2
  exit 1
fi

if [[ -f "$TARGET" ]]; then
  echo "Already exists: ${TARGET}"
  exit 0
fi

cp "$EXAMPLE" "$TARGET"
echo "Created ${TARGET} from example."
echo "Enable spytrend + magnific in Cursor Settings → Tools & MCP."
echo "Magnific uses OAuth — reload the server to sign in via browser."
