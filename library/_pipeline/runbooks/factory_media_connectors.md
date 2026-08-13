# Factory media connectors runbook

Unified entry point for Higgsfield, Perplexity Sonar, and fal queue clients used by the Creative Factory preset pipeline.

## Load environment

```bash
source library/_pipeline/orchestrator/load_env.sh
```

Sources, in order (runtime secrets from Cursor Cloud Agent win over files):

1. Injected runtime secrets (`HF_KEY`, `PERPLEXITY_API_KEY`, `FAL_KEY`, …)
2. `<repo>/.env`
3. `<repo>/library/_pipeline/.env`
4. `<repo>/library/_pipeline/secrets/<VAR>.key` (gitignored single-line files)

Quick wiring check:

```bash
bin/connect-factory
bin/connect-factory --strict   # exit 1 if any connector is down
```

## Required keys

| Variable | Client | Purpose |
|----------|--------|---------|
| `HF_KEY` | `tools/higgsfield_client.py` | Image/video generation |
| `PERPLEXITY_API_KEY` | `tools/perplexity_client.py` | Prompt research + enhance |
| `FAL_KEY` | `tools/fal_client.py` | fal queue models |

## Check all connectors

```bash
python3 library/_pipeline/orchestrator/preset_factory.py check-auth
```

## Preset catalog

```bash
python3 library/_pipeline/orchestrator/preset_factory.py list
python3 library/_pipeline/orchestrator/preset_factory.py validate
```

Catalog: `library/_pipeline/catalog/video_presets.json` (10 presets).

## Run a preset

```bash
python3 library/_pipeline/orchestrator/preset_factory.py run ugc_streamer_template \
  library/games/vs20olympgate/briefs/pilot-ad-v3/BRIEF.md \
  --game-id vs20olympgate --game-title "Gates of Olympus" --dry-run
```

## Creative enhancer (local)

Six flows with markdown templates under `library/_pipeline/enhancer/prompts/`:

- `streamer-character`, `streamer-board`, `streamer-clip`
- `ugc-character`, `ugc-board`, `ugc-clip`

```bash
python3 tools/creative_enhancer.py list
python3 tools/creative_enhancer.py enhance ugc-character "Casual creator discovers Gates of Olympus" \
  --vars '{"game_title":"Gates of Olympus","game_id":"vs20olympgate"}'
```

When `PERPLEXITY_API_KEY` is set, enhancer runs a Sonar pass after template render; otherwise template-only fallback.

## Perplexity commands

```bash
python3 tools/perplexity_client.py probe
python3 tools/perplexity_client.py research "Competitor slot ad hooks for Gates of Olympus"
python3 tools/perplexity_client.py enhance prompts/draft.md --context brief.md
python3 tools/perplexity_client.py async-sonar '[{"role":"user","content":"Deep research query"}]' --wait
```

## fal commands

```bash
python3 tools/fal_client.py check-auth
python3 tools/fal_client.py subscribe fal-ai/flux/schnell '{"prompt":"vertical slot ad b-roll"}'
```

## MCP integrations

Optional MCP servers (see `.cursor/mcp.json.example`):

- **SpyTrend** — competitor ad intelligence (`spytrend` tag in MVP roadmap)
- **Magnific** — upscaling / enhancement via MCP

## Agent skills

- `.agents/skills/higgsfield-connector/SKILL.md`
- `.agents/skills/factory-media-connectors/SKILL.md`
- `.agents/skills/ugc-flow/SKILL.md`
