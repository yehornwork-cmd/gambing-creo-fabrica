# Magnific MCP runbook

Optional MCP integration for AI upscaling and enhancement in the Creative Factory pipeline.

## Setup

1. Run `bash .cursor/setup-mcp.sh` (or copy `.cursor/mcp.json.example` → `.cursor/mcp.json`, gitignored).
2. Enable **magnific** in Cursor Settings → Tools & MCP.
3. Reload the server — Cursor opens OAuth in your browser; sign in with your Magnific account.

Magnific MCP uses **OAuth**, not an API key env var.

Example fragment:

```json
{
  "mcpServers": {
    "magnific": {
      "url": "https://mcp.magnific.com"
    }
  }
}
```

## When to use

- Upscale still frames exported from HyperFrames previews
- Enhance key art before Higgsfield image-to-video passes
- Recover detail on compressed screencast grabs

## Factory workflow

1. Render or export a frame from `hyperframes/` or `output/`.
2. Invoke Magnific MCP upscale tool on the asset path.
3. Pass the enhanced URL/path to `tools/higgsfield_client.py upload` if the model needs a hosted input.

## Fallback

If Magnific MCP is unavailable, document the gap in the run log and proceed with source resolution assets — do not block the MVP chunk.

## Related

- SpyTrend MCP: competitor ad snapshots (`spytrend` in `.cursor/mcp.json.example`)
- Factory connectors: `library/_pipeline/runbooks/factory_media_connectors.md`
