# SpyTrend snapshot — gates of olympus slot

- **generated:** 2026-08-13T04:27:06+00:00
- **source:** SpyTrend MCP (Pro linked account)
- **query_ads:** `gates of olympus slot`
- **total_ads_matching:** 737

## Ad listing patterns (sample)

| Title | Geo | CTA | Landing | Status | Run |
|-------|-----|-----|---------|--------|-----|
| Gates Of Olympus | CZ | Play game | onlyczgame.site | inactive | 19d |
| Gates Of Olympus | CZ | Play game | onlyczgame.site | inactive | 19d |
| Gates Of Olympus | CZ | Play game | onlyczgame.site | inactive | 19d |
| Gates Of Olympus | CZ | Play game | onlyczgame.site | inactive | 19d |
| Gates Of Olympus | CZ | Play game | onlyczgame.site | inactive | 19d |
| ⭐️⭐️⭐️⭐️⭐️ 5.0 | CA | Play game | oedgame.pics | vanished | 2d |
| ⭐️⭐️⭐️⭐️⭐️ 5.0 | CA | Play game | oedgame.pics | vanished | 1d |
| ⭐️⭐️⭐️⭐️⭐️ 5.0 | CA | Play game | oedonline.pics | vanished | 1d |
| ⭐️⭐️⭐️⭐️⭐️ 5.0 | CA | Play game | oedonline.pics | vanished | 1d |
| ⭐️⭐️⭐️⭐️⭐️ 5.0 | CA | Play game | oedonline.pics | vanished | 1d |

## Creative clusters (sample)

- **crash_and_plinko** · GB · active_today=0 · media=image
- **online_casino_slots** · US · active_today=1 · media=image
- **online_casino_slots** · BR · active_today=1 · media=image
- **online_casino_slots** · BR · active_today=1 · media=image
- **online_casino_slots** · US · active_today=4 · media=image
- **crash_and_plinko** · GB · active_today=0 · media=image
- **online_casino_slots** · LU,CA,AU,BE,DK,IT,FI,DE · active_today=1 · media=image
- **online_casino_slots** · CA · active_today=2 · media=image

## Hooks for factory briefs

1. **Star-rating social proof** — Meta ads use fake 5★ titles (`⭐️⭐️⭐️⭐️⭐️ 5.0`) with `Play game` CTA to affiliate landers (`*.pics`, `*.site`).
2. **Direct title match** — Some creatives name the slot (`Gates Of Olympus`) with geo-specific landers (CZ `onlyczgame.site`).
3. **UGC differentiation** — Competitors rarely show verified in-game screencast; our pilot uses real capture + VO beats — lean into authenticity.
4. **Scatter tease without false FS** — Competitors often over-promise bonus; our AD_B scenario explicitly avoids false bonus claims (see `gameplay/pilot_ad_scenario.md`).
5. **End-card compliance** — Pair excitement hooks with 18+ / responsible play on B06; most affiliate ads omit disclaimers.

## Factory actions

- Use `streamer_character_hook` / `ugc_streamer_template` presets with scatter-tease VO from scenario doc.
- SpyTrend refresh: `python3 tools/spytrend_snapshot.py --game-id vs20olympgate --query "gates of olympus slot"`
