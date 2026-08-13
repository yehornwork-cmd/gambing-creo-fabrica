# Constructor v0

Combinatorial engine for the iGaming creative factory. **500 creatives/day is a product of axes, not 500 hand-authored storyboards.**

```
games × scenarios × locales × formats × CTAs × winner clones
```

Default Gates matrix: `ru+pl × 9x16 × 2 CTAs` with geo locked to locale → **4 jobs** from one template. Stub formats (`1x1`, `16x9`) stay off until layouts exist.

## Layout

```
constructor/
├── schema/creative_job.schema.json   # CreativeJob + lineage
├── scenarios/                        # AD_B live; 5 catalog stubs
├── locale_packs/                     # ru seed, pl placeholder
├── ctas/catalog.json
├── variant_matrix.json               # axes + constraints
├── explode.py                        # 1 template → N jobs + HyperFrames batch
└── jobs/                             # generated CreativeJobs + batch.json
```

## Explode

```bash
python3 library/_pipeline/constructor/explode.py --dry-run
python3 library/_pipeline/constructor/explode.py
python3 library/_pipeline/constructor/test_explode.py
```

Writes `jobs/batch.json` for:

```bash
npx hyperframes render \
  --batch library/_pipeline/constructor/jobs/batch.json \
  --output "renders/{name}.mp4" \
  --strict-variables
```

(`hyperframes/` project promotion is F1 / P4.1 — today the template lives at `output/gates-pilot-ad-v3/`.)

## CreativeJob

Required fields: `game_id`, `scenario_id`, `locale`, `geo`, `format`, `cta_id`, `hook_id`, optional `parent_creative_id` (winner clones).

`lineage.beats[]` records which segment / `substitution_group` / `arc_slot_id` built the cut so a winner can be multiplied by swapping equivalent footage.

## What this is not

- Not a render farm. HyperFrames `--batch` / Cloud Run is the farm; this emits rows.
- Not TTS. Locale packs are overlay/VO strings only.
- Not a live Ads winner loop. Tag `parent_creative_id` by hand until F5.
