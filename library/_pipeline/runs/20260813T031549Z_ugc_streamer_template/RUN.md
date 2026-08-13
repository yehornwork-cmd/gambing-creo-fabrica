# UGC run 20260813T031549Z_ugc_streamer_template

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

## Brief

UGC creator discovers slot game

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
    "prompt": "# UGC character prompt\n\nYou are generating an **authentic UGC testimonial character** spot for a mobile game ad.\n\n## Inputs\n\n- Game: **Gates of Olympus** (`vs20olympgate`)\n- Aspect: **9:16**\n- Target duration: **15s**\n- Locale: **en**\n\n## Brief\n\nUGC creator discovers slot game\n\n## Output spec\n\nWrite a UGC-style prompt covering:\n\n1. **Talent** \u2014 relatable adult creator, natural lighting, phone-selfie or front-camera aesthetic.\n2. **Script beat** \u2014 casual first-person mention of discovering Gates of Olympus; curiosity, not income promises.\n3. **Setting** \u2014 everyday location (commute, couch, coffee break).\n4. **Authenticity cues** \u2014 slight imperfections, conversational tone, no studio polish.\n\nUnder 120 words. Plainspoken en voice if locale is not `en`. Entertainment-only disclaimer implied in tone."
  }
}
```
