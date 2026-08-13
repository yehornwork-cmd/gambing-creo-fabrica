# Capture connector runbook

Gameplay screencast capture via Hetzner worker.

## Environment

```bash
source library/_pipeline/orchestrator/load_env.sh
```

| Variable | Purpose |
|----------|---------|
| `CAPTURE_API_TOKEN` | Bearer token for worker API |
| `CAPTURE_WORKER_URL` | Default `http://127.0.0.1:8787`; production `http://65.108.48.54:8787` |

## Commands

```bash
python3 tools/capture_client.py check-auth
python3 tools/capture_client.py submit vs20olympgate --spins 80
python3 tools/capture_client.py status JOB_ID
python3 tools/capture_client.py wait JOB_ID
```

## When to recapture

`library/games/vs20olympgate/MANIFEST.json` → `capture_status.recapture_needed: true`

Missing segment: `seg_12_bonus_trigger` (FS bonus) for full AD_B arc.

## curl fallback

```bash
curl -s -X POST "${CAPTURE_WORKER_URL}/jobs/capture" \
  -H "Authorization: Bearer $CAPTURE_API_TOKEN" \
  -d '{"game_id":"vs20olympgate","spins":80}'
```
