# Higgsfield connector runbook

Factory CLI for the [Higgsfield platform API](https://docs.higgsfield.ai). Uses stdlib HTTP via `tools/media_http.py`.

## Base URL

```
https://platform.higgsfield.ai
```

Do **not** use `https://platform.platform.higgsfield.ai` (typo).

## Environment

```bash
source library/_pipeline/orchestrator/load_env.sh
export HF_KEY="YOUR_KEY_ID:YOUR_KEY_SECRET"
# or HF_API_KEY_ID + HF_API_KEY_SECRET
```

## Auth check

```bash
python3 tools/higgsfield_client.py check-auth
```

## Submit → poll → result

```bash
# Submit only
python3 tools/higgsfield_client.py submit higgsfield-ai/soul/standard \
  '{"prompt":"Editorial portrait in soft daylight","aspect_ratio":"9:16","resolution":"720p"}'

# Poll status
python3 tools/higgsfield_client.py status REQUEST_ID

# Submit and block until completed
python3 tools/higgsfield_client.py subscribe higgsfield-ai/soul/standard \
  '{"prompt":"UGC creator selfie, natural light"}'
```

## Upload input media

```bash
python3 tools/higgsfield_client.py upload ./input.jpg
# → {"public_url": "..."}
```

Pass `public_url` as `image_url`, `video_url`, or `audio_url` in model arguments.

## UGC preset runner

```bash
python3 library/_pipeline/orchestrator/higgsfield_ugc.py run library/games/vs20olympgate/briefs/pilot-ad-v3/BRIEF.md \
  --preset ugc_streamer_template --dry-run
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `401 Invalid credentials` | Rotate key in [Higgsfield Cloud](https://cloud.higgsfield.ai); verify `HF_KEY` format `id:secret` |
| SSL errors | Ensure `certifi` is installed (`pip install certifi`) — client uses certifi CA bundle |
| Timeout on subscribe | Increase `--poll-timeout`; check [status page](https://status.higgsfield.ai) |

## Agent skill

See `.agents/skills/higgsfield-connector/SKILL.md`.
