# Pilot ad scenario — gates-pilot-ad-v3 (AD_B partial)

**Game:** Gates of Olympus (`vs20olympgate`)  
**Scenario:** AD_B — partial arc (no FS in capture)  
**Trim map:** `gameplay/pilot_ad_trim_map_v2.json`  
**Storyboard:** `briefs/pilot-ad-v3/STORYBOARD.md`  
**Total runtime:** ~28.5s (25.5s gameplay + 3s end card)

---

## Narrative arc

Cold-open on **real screencast** with Russian VO. Build tumble energy → scatter tension (2/4, not triggered) → orb multiplier tease → win highlight using **actual € from capture** → compliance end card. Never claim bonus triggered.

---

## Beat script

| Beat | Duration | VO (RU) | Visual | Compliance |
|------|----------|---------|--------|------------|
| B01 Motion hook | 3.5s | «Gates of Olympus. Ставка €2. Поехали.» | Hard cut to spinning reels (`seg_v2_motion_hook` 48.0s) | No guaranteed win |
| B02 Tumble energy | 5.0s | «Каскад! Символы сыпятся…» | Tumble cascade (`seg_v2_tumble_spin`) | — |
| B03 Scatter tease | 6.0s | «Два scatter… ещё два — и бонус!» | 2 scatter on grid + optional 2/4 overlay | **Do not** say bonus triggered |
| B04 Orb build | 6.0s | «Orb! Множитель на поле…» | Multiplier orb lands | Visual FS fantasy OK, no false claim |
| B05 Win climax | 5.0s | Hint at big win / FS fantasy without false trigger | Use capture € amount | No inflated win |
| B06 End card | 3.0s | «Открой врата. Играй ответственно. 18+.» | Logo + CTA + disclaimer slots | GEO text from `compliance.json` |

---

## Capture dependencies

| Segment | Status | Action |
|---------|--------|--------|
| `seg_v2_motion_hook` | ✅ in analysis | Use trim map B01 |
| `seg_v2_tumble_spin` | ✅ | B02 |
| `seg_v2_scatter_proxy` | ✅ | B03 — 2 scatter only |
| `seg_v2_grid_full` / orb | ✅ | B04 |
| `seg_v2_climax_proxy` | ⚠️ fallback | B05 — may use v1 20-spin crop |
| `seg_12_bonus_trigger` | ❌ missing | **Recapture** with `capture_client.py` when token available |

---

## SpyTrend-informed hooks

From `intelligence/spytrend_snapshot.md`:

- Avoid fake 5★ rating tropes — differentiate with verified gameplay footage.
- Scatter tease is on-trend; pair with honest “not yet triggered” VO.
- End card must carry 18+ — most affiliate competitors skip this.

---

## Preset mapping

| Factory preset | Beat coverage |
|----------------|---------------|
| `ugc_streamer_template` | Full UGC testimonial wrapper around B01–B05 |
| `streamer_character_hook` | B01 cold open |
| `streamer_board_reveal` | B02–B04 board panels |
| `ugc_clip_reaction` | B05 reaction clip |

Dry-run:

```bash
python3 library/_pipeline/orchestrator/preset_factory.py run ugc_streamer_template \
  library/games/vs20olympgate/briefs/pilot-ad-v3/BRIEF.md \
  --game-id vs20olympgate --game-title "Gates of Olympus" --dry-run
```
