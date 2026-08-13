# UGC character prompt

You are generating an **authentic UGC testimonial character** spot for a mobile game ad.

## Inputs

- Game: **{{game_title}}** (`{{game_id}}`)
- Aspect: **{{aspect}}**
- Target duration: **{{duration_sec}}s**
- Locale: **{{locale}}**
- Competitor insight: {{competitor_hook}}

## Brief

{{brief}}

## Output spec

Write a UGC-style prompt covering:

1. **Talent** — relatable adult creator, natural lighting, phone-selfie or front-camera aesthetic.
2. **Script beat** — casual first-person mention of discovering {{game_title}}; curiosity, not income promises.
3. **Setting** — everyday location (commute, couch, coffee break).
4. **Authenticity cues** — slight imperfections, conversational tone, no studio polish.

Under 120 words. Plainspoken {{locale}} voice if locale is not `en`. Entertainment-only disclaimer implied in tone.
