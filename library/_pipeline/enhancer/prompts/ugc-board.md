# UGC storyboard prompt

You are generating a **UGC ad storyboard** frame sequence description for {{game_title}}.

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

Describe 3–4 sequential UGC panels in one consolidated prompt:

1. **Panel A** — creator introduces the game casually.
2. **Panel B** — over-the-shoulder gameplay glimpse (abstract reels, no literal UI clone).
3. **Panel C** — reaction / social-proof moment (friends watching, chat overlay placeholder).
4. **Panel D** — soft CTA frame with logo placeholder and 18+ slot.

Number each panel inline. Max 180 words total. Mobile-native vertical {{aspect}} composition throughout.
