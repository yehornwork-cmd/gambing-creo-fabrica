# MVP Roadmap — Creative Factory

Bounded chunks for PR-sized autopilot ticks. Status tracked in `library/_pipeline/state.json`.

Legend: `[ ]` pending · `[~]` in progress · `[x]` done · `[!]` blocked

---

## P0 — Pipeline bootstrap

| ID | Chunk | Acceptance |
|----|-------|------------|
| P0.1 | Orchestrator scaffold | `factory_run.py status/tick`, `AGENTS.md`, state schema |
| P0.2 | Dev environment | `.cursor/environment.json` + idempotent `install.sh` |

---

## P1 — Game library canonical layout

| ID | Chunk | Acceptance |
|----|-------|------------|
| P1.1 | Library schema | `library/README.md` + `library/games/_schema/` templates |
| P1.2 | Seed Gates of Olympus | `library/games/vs20olympgate/` from `context/gates-of-olympus/` |
| P1.3 | Path normalizer | `tools/path_normalizer.py` + audit script in repo |

---

## P2 — Capture integration

| ID | Chunk | Acceptance | Blocker |
|----|-------|------------|---------|
| P2.1 | Capture client | `tools/capture_client.py` + env docs | `CAPTURE_API_TOKEN` for live jobs |

---

## P3 — Segment analysis pipeline

| ID | Chunk | Acceptance |
|----|-------|------------|
| P3.1 | Trim map export | `gameplay/pilot_ad_trim_map_v2.json` wired from analysis |
| P3.2 | Scenario doc | `gameplay/pilot_ad_scenario.md` with VO beats |

---

## P4 — HyperFrames assembly

| ID | Chunk | Acceptance |
|----|-------|------------|
| P4.1 | Promote gates-pilot-ad-v3 | `hyperframes/gates-pilot-ad-v3/` from `output/` |
| P4.2 | Composition scenes | `compositions/scenes/b01–b06` stubs per STORYBOARD |

---

## P5 — Compliance layer

| ID | Chunk | Acceptance | Blocker |
|----|-------|------------|---------|
| P5.1 | Compliance schema | `compliance.json` template per GEO | GEO copy decisions |
| P5.2 | End-card placeholders | Disclaimer + CTA slots in end card scene | GEO copy decisions |

---

## P6 — Ad intelligence

| ID | Chunk | Acceptance |
|----|-------|------------|
| P6.1 | SpyTrend snapshot | Competitor vertical ad notes for Gates of Olympus (`spytrend` tag) |

---

## P7 — n8n automation hooks

| ID | Chunk | Acceptance |
|----|-------|------------|
| P7.1 | Factory tick webhook | `n8n/factory-tick.json` stub calling orchestrator |

---

## Current focus

Autopilot advances **one chunk per tick** in ID order, skipping `[!]` blocked chunks unless unblocked in state.

**Scale path is separate:** [FACTORY_SCALE.md](FACTORY_SCALE.md) (`F0`–`F5`). P1.3 (path normalizer) is hygiene — `tools/path_normalizer.py` and `tools/library_audit.py` already live in the repo. Do not treat finishing P1–P7 as the way to 500 creatives/day.

```bash
python3 library/_pipeline/orchestrator/factory_run.py tick --roadmap scale
```
