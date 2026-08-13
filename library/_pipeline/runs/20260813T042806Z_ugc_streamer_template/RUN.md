# UGC run 20260813T042806Z_ugc_streamer_template

- **preset:** ugc_streamer_template
- **game:** vs20olympgate
- **dry_run:** True

## Enhanced prompt

# UGC character prompt

You are generating an **authentic UGC testimonial character** spot for a mobile game ad.

## Inputs

- Game: **Gates of Olympus** (`vs20olympgate`)
- Aspect: **9:16**
- Target duration: **15s**
- Locale: **en**
- Competitor insight: **Star-rating social proof** — Meta ads use fake 5★ titles (`⭐️⭐️⭐️⭐️⭐️ 5.0`) with `Play game` CTA to affiliate landers (`*.pics`, `*.site`).
- Scenario: Cold-open on **real screencast** with Russian VO. Build tumble energy → scatter tension (2/4, not triggered) → orb multiplier tease → win highlight using **actual € from capture** → compliance end card. Never claim bonus triggered.
- Capture status: FS re-capture pending

## Brief

---
workflow: general-video
flow: automation
storyboard: yes
duration_target_sec: 30
aspect: "9:16"
resolution: "1080x1920"
scenario_id: AD_B
scenario_name: Gates Open
game_id: vs20olympgate
game_title: Gates of Olympus
provider: Pragmatic Play
locale_vo: ru
compliance_layer: user
---

# Gates of Olympus — Pilot Ad v3

## Intent

30s vertical perf ad assembled from **verified HQ screencast segments**. v3 replaces ffmpeg-only v2 with HyperFrames for overlays, VO sync, and variant iteration.

**Blocker for full AD_B:** current capture has no FS trigger (`bonus_triggered: false`). This cut uses available segments and honest VO — same constraint as pilot v2 audit.

## Assets

| Asset | Path (relative to game root) | Notes |
|-------|------------------------------|-------|
| Primary screencast | `assets/production/screencast/gates_of_olympus_bonus_hunt_hq.mp4` | v2 full-bleed 1080×1920 |
| Fallback screencast | `assets/production/screencast/gates_of_olympus_20spins_hq.mp4` | letterbox — avoid if v2 available |
| Segment map | `gameplay/game_analysis_v3.json` | `pilot_ad_trim_map_v2.beats` |
| Beat doc | `gameplay/pilot_ad_scenario.md` | VO + SFX per beat |
| End card | `assets/logo/logo_end_card_compliance_9x16.png` | 3s hold |
| Compliance rules | `compliance.json` | user validates GEO copy |

## Customizations

- Hard cuts between gameplay beats — no cross-dissolve
- Optional overlay: `2/4 SCATTER` counter on B03 (motion-graphics sub-comp)
- VO RU per `pilot_ad_scenario.md` beats B01–B06
- End card: logo + CTA placeholder + 18+ disclaimer placeholder

## Capture upgrade (when ready)

Re-capture on Hetzner with 80+ spins or Ante Bet until `bonus_triggered: true`, then replace B03–B05 with FS segments and unlock full AD_B arc.

```bash
curl -s -X POST http://capture-worker:8787/jobs/capture \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"game_id":"vs20olympgate","spins":80}'
```

## Run shape

- **flow:** automation — build from analysis + scenario, minimal questions
- **storyboard:** yes — review STORYBOARD.md before render
- **Render gate:** user approves preview before `hyperframes render`

## Output spec

Write a UGC-style prompt covering:

1. **Talent** — relatable adult creator, natural lighting, phone-selfie or front-camera aesthetic.
2. **Script beat** — casual first-person mention of discovering Gates of Olympus; curiosity, not income promises.
3. **Setting** — everyday location (commute, couch, coffee break).
4. **Authenticity cues** — slight imperfections, conversational tone, no studio polish.

Under 120 words. Plainspoken en voice if locale is not `en`. Entertainment-only disclaimer implied in tone.

## Higgsfield result

```json
{
  "dry_run": true,
  "endpoint": "higgsfield-ai/soul/standard",
  "arguments": {
    "aspect_ratio": "9:16",
    "resolution": "720p",
    "prompt": "# UGC character prompt\n\nYou are generating an **authentic UGC testimonial character** spot for a mobile game ad.\n\n## Inputs\n\n- Game: **Gates of Olympus** (`vs20olympgate`)\n- Aspect: **9:16**\n- Target duration: **15s**\n- Locale: **en**\n- Competitor insight: **Star-rating social proof** \u2014 Meta ads use fake 5\u2605 titles (`\u2b50\ufe0f\u2b50\ufe0f\u2b50\ufe0f\u2b50\ufe0f\u2b50\ufe0f 5.0`) with `Play game` CTA to affiliate landers (`*.pics`, `*.site`).\n- Scenario: Cold-open on **real screencast** with Russian VO. Build tumble energy \u2192 scatter tension (2/4, not triggered) \u2192 orb multiplier tease \u2192 win highlight using **actual \u20ac from capture** \u2192 compliance end card. Never claim bonus triggered.\n- Capture status: FS re-capture pending\n\n## Brief\n\n---\nworkflow: general-video\nflow: automation\nstoryboard: yes\nduration_target_sec: 30\naspect: \"9:16\"\nresolution: \"1080x1920\"\nscenario_id: AD_B\nscenario_name: Gates Open\ngame_id: vs20olympgate\ngame_title: Gates of Olympus\nprovider: Pragmatic Play\nlocale_vo: ru\ncompliance_layer: user\n---\n\n# Gates of Olympus \u2014 Pilot Ad v3\n\n## Intent\n\n30s vertical perf ad assembled from **verified HQ screencast segments**. v3 replaces ffmpeg-only v2 with HyperFrames for overlays, VO sync, and variant iteration.\n\n**Blocker for full AD_B:** current capture has no FS trigger (`bonus_triggered: false`). This cut uses available segments and honest VO \u2014 same constraint as pilot v2 audit.\n\n## Assets\n\n| Asset | Path (relative to game root) | Notes |\n|-------|------------------------------|-------|\n| Primary screencast | `assets/production/screencast/gates_of_olympus_bonus_hunt_hq.mp4` | v2 full-bleed 1080\u00d71920 |\n| Fallback screencast | `assets/production/screencast/gates_of_olympus_20spins_hq.mp4` | letterbox \u2014 avoid if v2 available |\n| Segment map | `gameplay/game_analysis_v3.json` | `pilot_ad_trim_map_v2.beats` |\n| Beat doc | `gameplay/pilot_ad_scenario.md` | VO + SFX per beat |\n| End card | `assets/logo/logo_end_card_compliance_9x16.png` | 3s hold |\n| Compliance rules | `compliance.json` | user validates GEO copy |\n\n## Customizations\n\n- Hard cuts between gameplay beats \u2014 no cross-dissolve\n- Optional overlay: `2/4 SCATTER` counter on B03 (motion-graphics sub-comp)\n- VO RU per `pilot_ad_scenario.md` beats B01\u2013B06\n- End card: logo + CTA placeholder + 18+ disclaimer placeholder\n\n## Capture upgrade (when ready)\n\nRe-capture on Hetzner with 80+ spins or Ante Bet until `bonus_triggered: true`, then replace B03\u2013B05 with FS segments and unlock full AD_B arc.\n\n```bash\ncurl -s -X POST http://capture-worker:8787/jobs/capture \\\n  -H \"Authorization: Bearer $TOKEN\" \\\n  -d '{\"game_id\":\"vs20olympgate\",\"spins\":80}'\n```\n\n## Run shape\n\n- **flow:** automation \u2014 build from analysis + scenario, minimal questions\n- **storyboard:** yes \u2014 review STORYBOARD.md before render\n- **Render gate:** user approves preview before `hyperframes render`\n\n## Output spec\n\nWrite a UGC-style prompt covering:\n\n1. **Talent** \u2014 relatable adult creator, natural lighting, phone-selfie or front-camera aesthetic.\n2. **Script beat** \u2014 casual first-person mention of discovering Gates of Olympus; curiosity, not income promises.\n3. **Setting** \u2014 everyday location (commute, couch, coffee break).\n4. **Authenticity cues** \u2014 slight imperfections, conversational tone, no studio polish.\n\nUnder 120 words. Plainspoken en voice if locale is not `en`. Entertainment-only disclaimer implied in tone."
  }
}
```
