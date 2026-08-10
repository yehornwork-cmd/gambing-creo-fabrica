# iGaming Creative Factory

Bridge repo for Cursor Cloud Agents.

## Structure
- `library/` — game library (Game DNA, segments, constructor builds)
- `tools/` — helper scripts (cursor_agent.py, path_normalizer.py)
- `hyperframes/` — HyperFrames projects
- `n8n/` — n8n workflow JSONs
- `docs/` — documentation

## Usage
This repo is used by Perplexity Computer to delegate coding tasks to Cursor Cloud Agents.
Perplexity pushes context/files to branches, Cursor agents clone and code, Perplexity pulls results.

