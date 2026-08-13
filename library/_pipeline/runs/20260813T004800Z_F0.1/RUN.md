# Constructor — F0.1

- **chunk:** F0.1 — CreativeJob + matrix + exploder
- **started:** 2026-08-13
- **status:** complete

## Acceptance

- [x] `library/_pipeline/constructor/schema/creative_job.schema.json` + template
- [x] Scenario catalog: live `AD_B` + stubs (hook, mechanic, bonus payoff, streamer PiP, UGC)
- [x] `variant_matrix.json` axes: locale × format × CTA × geo
- [x] `explode.py` emits CreativeJobs + HyperFrames `batch.json`
- [x] Pilot HTML uses `data-composition-variables` / `data-var-text`
- [x] `compliance.json` geo packs `ru` / `pl` (copy still human-gated)
- [x] Factory Scale roadmap F0–F5; P1.3 left as hygiene

## Assumptions

- First template: Gates of Olympus, 9:16, Meta/TikTok.
- Locales: `ru` seed from pilot; `pl` placeholder (SpyTrend sample was PL-heavy).
- Volume mix later: ~80% winner/template variants, ~20% new scenarios.
- Human approves GEO disclaimers and a QC sample, not every render.

## Blockers (not this chunk)

- `CAPTURE_API_TOKEN` for FS recapture (F2 / P2.1)
- User-validated GEO copy (P5 / F4)
