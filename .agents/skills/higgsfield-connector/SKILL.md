---
name: higgsfield-connector
description: Higgsfield platform API client for factory image/video generation. Use when submitting Higgsfield jobs, uploading inputs, polling status, or running UGC presets.
---

# Higgsfield connector

## When to use

- Generate images or video via Higgsfield platform models
- Upload local media for model input URLs
- Run UGC streamer presets from the factory catalog

## Prerequisites

```bash
source library/_pipeline/orchestrator/load_env.sh
export HF_KEY="KEY_ID:KEY_SECRET"
```

## CLI

```bash
python3 tools/higgsfield_client.py check-auth
python3 tools/higgsfield_client.py submit ENDPOINT JSON_ARGS
python3 tools/higgsfield_client.py status REQUEST_ID
python3 tools/higgsfield_client.py subscribe ENDPOINT JSON_ARGS
python3 tools/higgsfield_client.py upload ./file.jpg
```

Base URL: `https://platform.higgsfield.ai` (not `platform.platform.higgsfield.ai`).

## UGC runner

```bash
python3 library/_pipeline/orchestrator/higgsfield_ugc.py run BRIEF.md --preset ugc_streamer_template
```

## Runbook

Full troubleshooting: `library/_pipeline/runbooks/higgsfield_connector.md`

## Rules

- Never commit `HF_KEY` or secrets
- Use `--dry-run` on orchestrators before live spend
- Download outputs within retention window (≥7 days per Higgsfield docs)
