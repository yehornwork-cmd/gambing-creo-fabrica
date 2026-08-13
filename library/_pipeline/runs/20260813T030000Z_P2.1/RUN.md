# Run 20260813T030000Z_P2.1

- **chunk:** P2.1 — YouTube / Kick / Twitch sources
- **status:** complete (applied on Hetzner `/opt/igaming-library` + this repo)

## Actions

- Removed `/jobs/capture`, Playwright adapters, `batch_capture.py`, n8n capture workflow
- Discover/fetch/tick take `platforms=youtube,kick,twitch` (yt-dlp)
- Worker health: `capture_enabled: false`, `platforms: [youtube, kick, twitch]`
- Existing screencast MP4s left on disk as archive
