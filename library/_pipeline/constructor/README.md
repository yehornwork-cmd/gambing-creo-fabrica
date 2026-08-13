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
├── schema/creative_analysis.schema.json
├── scenarios/                        # AD_B, AD_HOOK_ONLY, AD_MECHANIC_SHOWCASE live; 3 stubs
├── locale_packs/                     # ru seed, pl placeholder, en fallback
├── geo_locale_map.json               # Forge buyer geos → locale packs + NL/PL gates
├── substitution_catalog.json         # F5.1 equivalent clips per group
├── ctas/catalog.json
├── variant_matrix.json               # axes + constraints
├── explode.py                        # 1 template → N jobs + HyperFrames batch
├── analyze_upload.py                 # buyer master → CreativeAnalysis (ffprobe)
├── multiply.py                       # analysis × geos → jobs with parent_creative_id
├── deep_analyze.py                   # Gemini native video beat rewrite
├── lint.py                           # blocked_claims QC
├── clone.py                          # substitution_group winner clones
└── jobs/                             # generated CreativeJobs + batch.json
```

## Buyer multiply (Forge)

```bash
python3 library/_pipeline/constructor/analyze_upload.py --video /path/master.mp4 --out /tmp/analysis.json
python3 library/_pipeline/constructor/multiply.py --analysis /tmp/analysis.json --geos PL,NL --dry-run
python3 library/_pipeline/constructor/test_multiply.py
```

Constructor: `clone.py` (F5.1), `lint.py` (F4.1), `deep_analyze.py` (F6.2). Live arcs: AD_B, AD_HOOK_ONLY, AD_MECHANIC_SHOWCASE.

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
- Not a live Ads winner loop. Buyer uploads set `parent_creative_id` (F6.1); substitution-group clones are still F5.1.
- Not demo-game capture. Footage comes from YouTube / Kick / Twitch VOD analysis.
