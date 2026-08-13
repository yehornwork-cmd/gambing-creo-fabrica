# Streamer character prompt

You are generating a **streamer-style talking-head character** for a short-form performance ad.

## Inputs

- Game: **{{game_title}}** (`{{game_id}}`)
- Aspect: **{{aspect}}**
- Target duration: **{{duration_sec}}s**
- Locale: **{{locale}}**
- Competitor insight: {{competitor_hook}}
- Scenario: {{scenario_summary}}
- Capture status: {{capture_note}}

## Brief

{{brief}}

## Output spec

Write a single Higgsfield-ready prompt describing:

1. **Character** — energetic streamer persona, wardrobe, lighting, camera angle (medium close-up).
2. **Hook line** — one spoken-style sentence teasing the game mechanic (no guaranteed-win claims).
3. **Background** — subtle gaming setup, RGB accents, depth of field.
4. **Compliance** — entertainment-only tone; no minors; no fake balance screenshots.

Keep under 120 words. Imperative visual language. No markdown headings in the final prompt body.
