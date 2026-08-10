# STORYBOARD — gates-pilot-ad-v3

**Game:** Gates of Olympus · **Scenario:** AD_B (partial — no FS in capture)  
**Source:** `gameplay/game_analysis_v3.json` · **Total:** ~28.5s + end card

---

## Frame 1 · B01 Motion hook

- **status:** outline
- **src:** compositions/scenes/b01-hook.html
- **duration:** 3.5s
- **trim:** analysis `pilot_ad_trim_map_v2` beat B01 or seg_v2_motion_hook (48.0→51.5)
- **blueprint:** gameplay clip — hard cut in, no idle splash
- **beat:** Cold open on spinning reels. VO: «Gates of Olympus. Ставка €2. Поехали.»
- **tags:** `motion_hook`, `spin_button_press`

## Frame 2 · B02 Tumble energy

- **status:** outline
- **src:** compositions/scenes/b02-tumble.html
- **duration:** 5.0s
- **trim:** seg_v2_tumble_spin or B02 beat from trim map
- **blueprint:** gameplay clip
- **beat:** Tumble cascade, gems falling. VO: «Каскад! Символы сыпятся…»
- **tags:** `tumble_chain`, `cluster_win`

## Frame 3 · B03 Scatter tease

- **status:** outline
- **src:** compositions/scenes/b03-scatter.html
- **duration:** 6.0s
- **trim:** seg_v2_scatter_proxy (54.0→60.0)
- **blueprint:** gameplay clip + optional overlay sub-comp (`2/4 SCATTER` counter)
- **beat:** 2 scatter on grid — tension, not false 3-scatter claim. VO: «Два scatter… ещё два — и бонус!»
- **tags:** `scatter_tease`, `bonus_tease`
- **⚠️** Do not VO "bonus triggered" — FS not in capture

## Frame 4 · B04 Orb multiply build

- **status:** outline
- **src:** compositions/scenes/b04-orb.html
- **duration:** 6.0s
- **trim:** from trim map B04
- **blueprint:** gameplay clip
- **beat:** Multiplier orb lands. VO: «Orb! Множитель на поле…»
- **tags:** `multiplier_orb`, `global_multiplier_fs` (visual only)

## Frame 5 · B05 Win climax

- **status:** outline
- **src:** compositions/scenes/b05-climax.html
- **duration:** 5.0s
- **trim:** from trim map B05
- **blueprint:** gameplay clip
- **beat:** Tumble win on screen — use actual € from capture, not inflated. VO hints at FS fantasy without false claim.
- **tags:** `cluster_win`, `win_highlight`

## Frame 6 · B06 End card

- **status:** outline
- **src:** compositions/scenes/b06-endcard.html
- **duration:** 3.0s
- **asset:** `assets/logo/logo_end_card_compliance_9x16.png`
- **blueprint:** logo-reveal / static hold
- **beat:** Logo + CTA + 18+ disclaimer placeholder. VO: «Открой врата. Играй ответственно. 18+.»
- **compliance:** user finalizes GEO text per `compliance.json`
