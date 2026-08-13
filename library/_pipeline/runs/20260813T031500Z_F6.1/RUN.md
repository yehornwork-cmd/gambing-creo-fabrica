# Run 20260813T031500Z_F6.1

- **chunk:** F6.1 — Upload → analyze → multiply plan
- **started:** 2026-08-13T03:15:00+00:00
- **status:** complete

## Acceptance

- [x] `analyze_upload.py` probes a master (ffprobe) and scales AD_B beats onto its duration
- [x] `multiply.py` explodes Forge geos × CTAs with `parent_creative_id`
- [x] Worker `POST /jobs/buyer/multiply` (sync) + optional `buyer_deep` signals
- [x] Forge `submitRun` calls the worker before n8n and stores the variant plan on the run
- [x] `python3 library/_pipeline/constructor/test_multiply.py`

## Actions

- Added constructor buyer loop next to explode (does not replace VOD discover).
- Live Hetzner constructor `arcs/` / `builds/` left in place; git files copied alongside.
- Forge generate copy: upload → разбор → размножение → рендер.

## Assumptions

- Fast path is heuristic beats (AD_B slots scaled to duration), not Gemini dual. Dual stays on VOD corpus.
- n8n still renders MP4s; constructor jobs are the plan + lineage for later HyperFrames/F5 clones.
- NL and other Forge geos without a locale pack fall back to English CTA copy; n8n writes market VO.

## Blockers

- None for the plan. Paid-media GEO copy remains human-gated (F4).
