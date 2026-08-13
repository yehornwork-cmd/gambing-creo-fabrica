# iGaming Creative Factory

Bridge repo for Cursor Cloud Agents.

## Structure
- `library/` — game library (Game DNA, segments, constructor builds)
- `library/_pipeline/constructor/` — CreativeJob schema, scenario catalog, variant matrix
- `tools/` — helper scripts (path_normalizer.py, explode via constructor)
- `hyperframes/` — HyperFrames projects
- `n8n/` — n8n workflow JSONs
- `docs/` — documentation

## Factory scale

500 creatives/day is combinatorial (`locale × format × CTA × scenario`), not 500 unique storyboards. See `library/_pipeline/phases/FACTORY_SCALE.md` and `library/_pipeline/constructor/README.md`.

```bash
python3 library/_pipeline/constructor/explode.py --dry-run
python3 library/_pipeline/constructor/test_multiply.py
python3 library/_pipeline/orchestrator/factory_run.py status
```

Buyer path (forge.vizioner.xyz): upload a winner → `analyze_upload.py` + `multiply.py` → n8n renders. See `library/_pipeline/BUYER_LOOP.md`. Keys: `library/_pipeline/SECRETS.md` (Hetzner `.env` / n8n Credentials, never this repo).

## Usage
This repo is used by Perplexity Computer to delegate coding tasks to Cursor Cloud Agents.
Perplexity pushes context/files to branches, Cursor agents clone and code, Perplexity pulls results.

