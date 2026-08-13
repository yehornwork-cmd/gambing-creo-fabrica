# Marathon session 4 — daemon + CI

- `bin/marathon-daemon` running in tmux — polls every 5min for media keys
- On `connect-factory --strict` success: auto-executes `ugc_streamer_template` live
- GitHub Actions: `preset-batch.yml` validates 10 presets on every PR
- `bin/marathon-status` — one-command progress summary

Daemon log: `library/_pipeline/runs/marathon_daemon.log` (gitignored, local only)
