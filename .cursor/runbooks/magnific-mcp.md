# Magnific MCP runbook

Optional MCP integration for AI upscaling and enhancement in the Creative Factory pipeline.

## Setup

1. Copy `.cursor/mcp.json.example` → `.cursor/mcp.json` (gitignored).
2. Set `MAGNIFIC_API_KEY` in repo `.env` or `library/_pipeline/.env`.
3. Enable **magnific** in Cursor Settings → Tools & MCP.

Example fragment:

```json
{
  "mcpServers": {
    "magnific": {
      "url": "https://mcp.magnific.ai/mcp",
      "headers": {
        "Authorization": "Bearer ${MAGNIFIC_API_KEY}"
      }
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
