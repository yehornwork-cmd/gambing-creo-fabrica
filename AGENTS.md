# Creative Factory — Agent Instructions

Autonomous cloud agents run bounded MVP chunks via the factory orchestrator.

## Quick start

```bash
python3 library/_pipeline/orchestrator/factory_run.py status
python3 library/_pipeline/orchestrator/factory_run.py tick
python3 library/_pipeline/orchestrator/factory_run.py tick --roadmap scale
```

After `tick`, implement **exactly one** PR-sized chunk from the returned run log. Commit, push to `cursor/*`, and update the PR.

Scale work (`F0`–`F5`) lives in `library/_pipeline/phases/FACTORY_SCALE.md` and `library/_pipeline/constructor/`. MVP `P*` chunks bootstrap the bridge; they are not the 500/day factory.

## Repo layout

| Path | Purpose |
|------|---------|
| `library/games/<game_id>/` | Canonical Game DNA, gameplay analysis, assets refs |
| `library/_pipeline/` | Orchestrator, MVP + Factory Scale roadmaps, run logs |
| `library/_pipeline/constructor/` | CreativeJob schema, scenario catalog, variant matrix, exploder |
| `hyperframes/` | Renderable HyperFrames projects |
| `tools/` | Helper scripts (path normalizer) |
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
| Compliance copy | GEO-specific disclaimers, 18+ text, CTA legality |
| Ambiguous business reqs | Target GEO, brand voice, budget caps |

Everything else: make a reasonable default, document the assumption in the run log, and ship.

## Material sources

Demo-game capture is retired. Gameplay and streamer beats come from **YouTube / Kick / Twitch VOD analysis** on Hetzner (`POST /jobs/youtube/tick` with `platforms: "youtube,kick,twitch"`). Buyer masters on **forge.vizioner.xyz** use `POST /jobs/buyer/multiply` (ffprobe + constructor explode). See [BUYER_LOOP.md](library/_pipeline/BUYER_LOOP.md) and [CONNECTORS.md](library/_pipeline/CONNECTORS.md). Do not fabricate bonus/FS claims that are not in an analyzed clip.

## Ad intelligence (SpyTrend)

When a chunk tags `spytrend`, query SpyTrend MCP for competitor vertical ads (Meta archive is fine on demo tier). Save a markdown snapshot to the run log — do not block the chunk on paid media fetches.

## Git workflow

- Work on `cursor/*` branches only.
- No secrets in the repo.
- Perplexity merges after QA.
