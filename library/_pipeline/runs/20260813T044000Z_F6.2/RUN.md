# Run 20260813T044000Z_F6.2

- **chunks:** F6.2, F3.1, F4.1, F5.1
- **started:** 2026-08-13T04:40:00+00:00
- **status:** complete (constructor + worker; Forge overlay to apply on Hetzner)

## Acceptance

- [x] F3.1 `AD_HOOK_ONLY` and `AD_MECHANIC_SHOWCASE` have beats + template (`status: partial`)
- [x] F4.1 `lint.py` blocks guaranteed-win copy; NL/PL buyer geos `status: blocked` unless `compliance_allow`
- [x] F5.1 `clone.py` swaps `substitution_group` segment_ids with `parent_creative_id`
- [x] F6.2 `deep_analyze.py` merges Gemini native-video beats; heuristic kept on failure
- [x] Duration pick: `<8s` hook, `8–18s` mechanic, else AD_B
- [x] `python3 library/_pipeline/constructor/test_*.py`

## Assumptions

- `compliance_allow` defaults false. If every selected GEO is on hold, n8n still receives the original geos so the farm produces preview files; the run notice marks hold.
- Mixed batches (e.g. CA-EN + NL) send only ready geos to n8n.
- Whisper skipped: worker image has no ASR wheel; Gemini native video already hears the clip.
- F1.1 HyperFrames `--batch` blocked on Hetzner Node 18 vs CLI Node 22.

## Next

Apply overlay + copy constructor onto `/opt/igaming-library`, restart `youtube-worker`, smoke `/jobs/buyer/multiply`.
