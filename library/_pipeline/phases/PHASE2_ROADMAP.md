# Phase 2 — Media generation & render

Post-MVP work after `state.json` marks P0–P7 complete.

| ID | Chunk | Acceptance | Blocker |
|----|-------|------------|---------|
| P8.1 | Live connector auth | `bin/connect-factory --strict` passes | `HF_KEY`, `PERPLEXITY_API_KEY`, `FAL_KEY` |
| P8.2 | UGC preset execute | One `ugc_streamer_template` Higgsfield job completes | P8.1 |
| P8.3 | FS re-capture | New screencast with `bonus_triggered: true` | `CAPTURE_API_TOKEN` |
| P8.4 | Full AD_B arc | Update trim map + scenario for FS segments | P8.3 |
| P8.5 | HyperFrames render | Export final MP4 from `hyperframes/gates-pilot-ad-v3/` | P8.4 |
| P8.6 | SpyTrend refresh | Weekly snapshot + hook diff in intelligence/ | None |
| P8.7 | Magnific upscale | Key frames enhanced via MCP | OAuth in Cursor |
| P8.8 | n8n production | Deploy `factory-tick.json` on worker with secrets | Infra |

Add rows here as new bounded chunks; run `factory_run.py tick` after extending roadmap parser or manual runs.
