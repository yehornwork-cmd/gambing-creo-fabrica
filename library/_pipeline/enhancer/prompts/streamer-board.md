# Streamer storyboard prompt

You are generating a **streamer ad storyboard panel** for a vertical performance creative.

## Inputs

- Game: **{{game_title}}** (`{{game_id}}`)
- Aspect: **{{aspect}}**
- Target duration: **{{duration_sec}}s**
- Locale: **{{locale}}**

## Brief

{{brief}}

## Output spec

Produce one image-generation prompt that reads like a storyboard frame:

1. **Layout** — labeled zones for gameplay insert, streamer PiP, and lower-third CTA placeholder.
2. **Beat** — which story beat this panel covers (hook, tension, payoff, or end-card).
3. **Motion hint** — static frame plus one arrow/note for intended camera or cut direction.
4. **Brand** — slot game aesthetic matching {{game_title}} without copying trademark art literally.

Use concise art-direction bullets merged into a flowing prompt (max 150 words). Avoid compliance violations and guaranteed outcomes.
