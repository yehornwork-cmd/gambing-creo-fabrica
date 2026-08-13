# Creative Factory — Agent Instructions

Autonomous cloud agents run bounded MVP chunks via the factory orchestrator.

## Quick start

```bash
python3 library/_pipeline/orchestrator/factory_run.py status
python3 library/_pipeline/orchestrator/factory_run.py tick
```

After `tick`, implement **exactly one** PR-sized chunk from the returned run log. Commit, push to `cursor/*`, and update the PR.

## Repo layout

| Path | Purpose |
|------|---------|
| `library/games/<game_id>/` | Canonical Game DNA, gameplay analysis, assets refs |
| `library/_pipeline/` | Orchestrator, MVP roadmap, run logs |
| `hyperframes/` | Renderable HyperFrames projects |
| `tools/` | Helper scripts (path normalizer, capture client, media connectors) |
| `context/` | Staging area — migrate into `library/` then deprecate |
| `output/` | Render previews (promote to `hyperframes/` when approved) |
| `n8n/` | Automation workflow JSONs |
| `docs/` | Human-facing documentation |

## Orchestration rules

1. **One chunk per tick** — do not batch multiple MVP chunks in a single PR.
2. **Cheap models for orchestration** — use Composer / lightweight models for `status`, `tick`, and run logging; reserve heavy models for creative/render work only when a chunk requires it.
3. **No open-ended rebuilds** — if a chunk scope creeps, stop and split it in `MVP_ROADMAP.md` instead of expanding the PR.
4. **Log every run** under `library/_pipeline/runs/<run_id>/` with `RUN.md` (intent, actions, blockers, next).
5. **Prefer existing conventions** — match patterns in `library/games/` and HyperFrames skills under `context/hf-skills/`.

## Blockers — ask the human only for

| Blocker | Env / decision needed |
|---------|----------------------|
| Capture jobs | `CAPTURE_API_TOKEN` for Hetzner worker (`65.108.48.54:8787`) |
| Media generation | `HF_KEY`, `PERPLEXITY_API_KEY`, `FAL_KEY` — see `bin/connect-factory` |
| Compliance copy | GEO-specific disclaimers, 18+ text, CTA legality |
| Ambiguous business reqs | Target GEO, brand voice, budget caps |

Everything else: make a reasonable default, document the assumption in the run log, and ship.

## Ad intelligence (SpyTrend)

When a chunk tags `spytrend`, query SpyTrend MCP for competitor vertical ads (Meta archive is fine on demo tier). Save a markdown snapshot to the run log — do not block the chunk on paid media fetches.

## Capture upgrade path

When `bonus_triggered: false` in analysis, note `recapture_needed` in the run log. Do not fabricate FS footage. Re-capture via:

```bash
curl -s -X POST http://65.108.48.54:8787/jobs/capture \
  -H "Authorization: Bearer $CAPTURE_API_TOKEN" \
  -d '{"game_id":"vs20olympgate","spins":80}'
```

## Git workflow

- Work on `cursor/*` branches only.
- No secrets in the repo.
- Perplexity merges after QA.
