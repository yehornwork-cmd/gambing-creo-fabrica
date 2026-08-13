# Buyer loop — forge.vizioner.xyz

Buyers get results fast by **analyzing the video they upload**, then **multiplying** it into market × CTA jobs. The n8n farm still renders the MP4s; the constructor plan is ready in seconds.

```
upload (Forge /media)
    → POST /jobs/buyer/multiply   (youtube-worker, internal)
        ffprobe + AD_B beats scaled to duration
        explode locale × CTA with parent_creative_id
    → buyer sees N variants immediately
    → n8n webhook localizes/renders MP4s (existing farm)
    → optional extract_signals --skip-ocr (deep_job_id)
```

## Why this exists

Forge already had «загрузить мастер → выбрать GEO → n8n». That path does not **read** the clip. Without analysis there is nothing to multiply: no beats, no substitution groups, no `parent_creative_id`. 500/day is combinatorial clones of a winner, not 500 unique storyboards.

Keys and file formats: [SECRETS.md](SECRETS.md). Worker token is `CAPTURE_API_TOKEN`; Forge uses the same value as `WORKER_TOKEN`. Never commit `.env` or `secrets/gemini.key`.

## Worker API (localhost / docker, Bearer `CAPTURE_API_TOKEN`)

`POST /jobs/buyer/multiply`

```json
{
  "source_url": "https://forge.vizioner.xyz/media/master%2F….mp4",
  "geos": ["PL", "NL"],
  "product": "Gates of Olympus",
  "deep_analyze": true
}
```

Response (sync, typically 1–3s): `analysis` (probe + 6 scaled beats) + `jobs[]` (geo × CTA) + optional `deep_job_id`.

Allowed download hosts: `forge`, `forge.vizioner.xyz`, `*.vizioner.xyz`.

## Constructor

```bash
python3 library/_pipeline/constructor/analyze_upload.py --video /path/master.mp4
python3 library/_pipeline/constructor/multiply.py --analysis analysis.json --geos PL,NL --dry-run
python3 library/_pipeline/constructor/test_multiply.py
```

Artifacts on Hetzner: `/opt/igaming-library/_pipeline/buyer_uploads/<analysis_id>/`.

## Forge wiring

`submitRun` calls the worker **before** n8n, stores `analysis` / `multiply` on the run report, then fires the existing factory webhook so files still land in Drive / library.
