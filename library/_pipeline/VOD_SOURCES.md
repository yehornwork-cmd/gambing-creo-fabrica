# VOD sources — YouTube, Kick, Twitch

Demo-game Playwright capture is **retired**. Gameplay and streamer material come from existing VODs.

Canonical worker lives on Hetzner (`root@65.108.48.54`, `youtube-worker`, `127.0.0.1:8787`):

| Endpoint | Role |
|----------|------|
| `POST /jobs/youtube/tick` | discover → fetch → dual → material |
| Body `platforms` | `youtube,kick,twitch` (default) |
| `POST /jobs/youtube/material` | atlases + clip library on raw VODs |

`/jobs/capture` is gone. Existing screencast MP4s under `/opt/igaming-library/Pragmatic_Play/.../screencast/` stay as archive only.

FS / bonus payoff beats must come from **analyzed VOD clips**, not from spinning a demo.
