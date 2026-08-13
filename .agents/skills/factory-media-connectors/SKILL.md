---
name: factory-media-connectors
description: Orchestrate Creative Factory media connectors (Higgsfield, Perplexity, fal) and video presets. Use when running preset_factory, creative_enhancer, or checking connector auth.
---

# Factory media connectors

## When to use

- List, validate, or run presets from `library/_pipeline/catalog/video_presets.json`
- Enhance briefs into model-ready prompts (template + optional Perplexity)
- Verify all connector credentials before a factory tick

## Quick start

```bash
bin/connect-factory              # status (non-fatal)
bin/connect-factory --strict   # fail if any connector missing
source library/_pipeline/orchestrator/load_env.sh
python3 library/_pipeline/orchestrator/preset_factory.py check-auth
python3 library/_pipeline/orchestrator/preset_factory.py list
python3 library/_pipeline/orchestrator/preset_factory.py validate
```

Credentials load from: Cursor runtime secrets → `.env` → `library/_pipeline/secrets/*.key`

## Run preset

```bash
python3 library/_pipeline/orchestrator/preset_factory.py run PRESET_ID BRIEF.md \
  --game-id vs20olympgate --game-title "Gates of Olympus"
```

Add `--dry-run` to skip live API submission.

## Enhancer flows

| Flow | Template |
|------|----------|
| streamer-character | `library/_pipeline/enhancer/prompts/streamer-character.md` |
| streamer-board | `library/_pipeline/enhancer/prompts/streamer-board.md` |
| streamer-clip | `library/_pipeline/enhancer/prompts/streamer-clip.md` |
| ugc-character | `library/_pipeline/enhancer/prompts/ugc-character.md` |
| ugc-board | `library/_pipeline/enhancer/prompts/ugc-board.md` |
| ugc-clip | `library/_pipeline/enhancer/prompts/ugc-clip.md` |

```bash
python3 tools/creative_enhancer.py enhance ugc-character "Brief text here"
```

## Clients

| Tool | Env var |
|------|---------|
| `tools/higgsfield_client.py` | `HF_KEY` |
| `tools/perplexity_client.py` | `PERPLEXITY_API_KEY` |
| `tools/fal_client.py` | `FAL_KEY` or `~/.fal/auth0_token` |
| `tools/capture_client.py` | `CAPTURE_API_TOKEN` |
| `tools/spytrend_snapshot.py` | SpyTrend OAuth via `bin/spytrend-token.sh` |

All HTTP via `tools/media_http.py` (stdlib + certifi).

## Runbook

`library/_pipeline/runbooks/factory_media_connectors.md`
