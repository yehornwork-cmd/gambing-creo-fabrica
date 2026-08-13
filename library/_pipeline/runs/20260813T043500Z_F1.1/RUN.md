# Run 20260813T043500Z_F1.1

- **chunk:** F1.1 — Two locales × two CTAs via HyperFrames `--batch`
- **started:** 2026-08-13T04:31:00+00:00
- **status:** complete (on Node 22 agent VM; not on Hetzner host Node 18)

## Acceptance

- [x] `npx hyperframes render --batch jobs/batch.json` → 4 MP4s, manifest `failed: 0`
- [x] Duration 28.5s, 1080×1920, draft quality (~5.5 MB each)
- [x] Wrapper: `python3 library/_pipeline/constructor/render_batch.py`

Outputs (gitignored): `output/renders/vs20olympgate_AD_B_{ru,pl}_{ru,pl}_9x16_{play_now,bonus_first_deposit}.mp4`

## Notes

Live buyer delivery remains n8n + `forge-renderer`. Promote HyperFrames to the VPS only after Node ≥ 22 is on the render host.
