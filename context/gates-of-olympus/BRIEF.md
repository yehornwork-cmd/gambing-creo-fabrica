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
