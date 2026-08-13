# Cursor Cloud Agent Bridge Repo

## Connected
- Perplexity Computer: orchestrator
- Cursor Cloud Agents: coding executor
- n8n (n8n.vizioner.xyz): automation
- Hetzner VOD worker (65.108.48.54): YouTube / Kick / Twitch analysis (`127.0.0.1:8787`)
- Forge (forge.vizioner.xyz): buyer upload → analyze → multiply → n8n render

## Rules
- Agents work on `cursor/*` branches
- Perplexity merges after QA
- No secrets in this repo

