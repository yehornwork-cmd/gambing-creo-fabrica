---
name: ugc-flow
description: UGC video preset flow for factory streamer/testimonial creatives. Prefer Supercomputer MCP when available; otherwise use higgsfield_ugc orchestrator.
---

# UGC flow

## When to use

- Produce UGC-style talking-head or reaction clips for game ads
- Run the `ugc_streamer_template` catalog preset

## Preferred path — Supercomputer MCP

When the **Supercomputer** MCP server is connected in Cursor, use its tools for end-to-end UGC generation, asset management, and timeline placement instead of raw CLI.

Check MCP availability: **Cursor Settings → Tools & MCP**.

## Fallback — factory orchestrator

```bash
source library/_pipeline/orchestrator/load_env.sh
python3 library/_pipeline/orchestrator/higgsfield_ugc.py run BRIEF.md \
  --preset ugc_streamer_template --dry-run
```

Enhancer flow: `ugc-character` → Higgsfield subscribe.

## Related

- Preset catalog: `library/_pipeline/catalog/video_presets.json`
- Skill: `.agents/skills/higgsfield-connector/SKILL.md`
- Runbook: `library/_pipeline/runbooks/factory_media_connectors.md`
