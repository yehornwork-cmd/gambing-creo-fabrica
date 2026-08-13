# Forge overlay (forge.vizioner.xyz)

Live app is **not** this git repo. It lives on Hetzner at `/opt/forge/src/app/app` (container `forge-forge-1`, Caddy `forge.vizioner.xyz` → `:8811`).

This directory versions the buyer-loop patches so the next agent can re-apply them:

| Overlay file | Live path |
|--------------|-----------|
| `overlay/factory.server.ts` | `src/lib/factory.server.ts` |
| `overlay/data.submitRun.patch.ts` | fragment for `src/lib/api/data.ts` |
| `overlay/types.snippet.ts` | fields on `RunReportShape` |
| `overlay/generate.copy.md` | copy changes for `src/routes/app/generate.tsx` |

Do **not** copy secrets. Worker token is `WORKER_TOKEN` in `/opt/forge/.env` (same value as worker `CAPTURE_API_TOKEN`, never committed).
