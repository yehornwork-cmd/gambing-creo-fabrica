# Factory Scale Roadmap

Path from one Gates pilot to ~500 quality creatives/day. Status tracked in `library/_pipeline/state.json` (`completed` holds both `P*` and `F*` ids).

500/day is combinatorial: `games × scenarios × locales × formats × CTAs × winner clones`. Do not treat this as 500 unique storyboards.

Legend: `[ ]` pending · `[x]` done · `[!]` blocked

MVP bootstrap (`P0`–`P7` in [MVP_ROADMAP.md](MVP_ROADMAP.md)) still exists. **P1.3 path normalizer is hygiene** (`tools/path_normalizer.py` + `tools/library_audit.py` already in repo) — not the scale path. Tick MVP chunks with `factory_run.py tick`; tick scale chunks with `factory_run.py tick --roadmap scale`.

---

## F0 — Constructor schema

| ID | Chunk | Acceptance |
|----|-------|------------|
| F0.1 | CreativeJob + matrix + exploder | `library/_pipeline/constructor/` with schema, AD_B catalog, variant matrix, `explode.py` emitting HyperFrames batch rows |

---

## F1 — Golden path variants

| ID | Chunk | Acceptance |
|----|-------|------------|
| F1.1 | Two locales × two CTAs render | One template renders 4 jobs (`ru/pl` × `play_now` / `bonus_first_deposit`) via `hyperframes render --batch` |

---

## F2 — VOD inventory

| ID | Chunk | Acceptance |
|----|-------|------------|
| F2.1 | YouTube + Kick + Twitch discover | Tick discovers/fetches from all three platforms; bonus/FS beats come from analyzed clips, not demo recapture |

---

## F3 — Scenario catalog fill

| ID | Chunk | Acceptance |
|----|-------|------------|
| F3.1 | Live arcs beyond AD_B | At least one additional scenario (`AD_HOOK_ONLY` or `AD_MECHANIC_SHOWCASE`) has beats + template, not `status: stub` |

---

## F4 — QC gates

| ID | Chunk | Acceptance |
|----|-------|------------|
| F4.1 | Lint + compliance + sample review | Batch jobs fail on `blocked_claims`; NL/PL buyer geos are `status: blocked` unless `compliance.allow`; human reviews a sample, not every render |

---

## F5 — Winner multiply

| ID | Chunk | Acceptance |
|----|-------|------------|
| F5.1 | Clone via substitution groups | `parent_creative_id` + equivalent `substitution_group` segments explode a tagged winner into N variants |

---

## F6 — Buyer loop (forge.vizioner.xyz)

| ID | Chunk | Acceptance |
|----|-------|------------|
| F6.1 | Upload → analyze → multiply plan | Buyer master on Forge is probed, beats are mapped, locale × CTA jobs land in `<10s`; n8n still renders MP4s |
| F6.2 | Deep Gemini + GEO hold | Async `buyer_deep` rewrites heuristic beats via Gemini native video. GEO hold is deferred — generator ships all requested markets |

---

## Current focus

F1.1 HyperFrames `--batch` of the 4-job Gates matrix is proven on Node 22 (`render_batch.py`). Live Hetzner host is still Node 18 — buyer MP4s stay on n8n + forge-renderer until the render host is upgraded.
