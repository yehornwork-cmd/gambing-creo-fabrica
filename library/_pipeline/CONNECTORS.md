# Connector research — how to actually multiply buyer winners

Research date: 2026-08-13. Method: live **Perplexity Multi Gateway** (`sonar-pro`, 4 parallel queries via `POST /webhook/pplx-multi-qa`) plus inventory of n8n workflows/credentials on Hetzner. Exa MCP was rate-limited; public docs used as secondary cites.

**Operating rule from Perplexity (and every 2026 factory write-up):** keep the winning master. Fan out **text / VO / CTA / crop / end-card**. Do not reshoot or generate a new storyboard per geo. Generative video (Higgsfield / Kling / Runway / HeyGen) is an exception layer for a new hook, not the default path.

## What we already have (wired)

| Connector | Where | Role today |
|-----------|--------|------------|
| Perplexity `sonar-pro` | `pplx-multi-qa`, GEO Research → Factory | Research, GEO copy notes |
| OpenAI Chat | PC-07, Factory v3 «Тексты» | Headlines / CTA copy |
| OpenAI TTS | Factory v3, Factory v5, `tts-gen` | Localized VO |
| OpenAI Vision | PC-07V `/llm-vision` | Frame-level vision |
| Gemini Vision | PC-26 `/creative-qa`, youtube-worker | QA + VOD dual analysis |
| SpyTrend MCP | R41 gateway (`mcp.spytrend.com`) | Competitor Meta ads |
| Google Drive | Factory v3/v5 | Delivery |
| ffmpeg compositor | Factory v5, `forge-renderer:8890` | Headline + disclaimer + VO on master |
| Layout analyzer | Factory v3 → `creative-localizer.vercel.app` | Overlay boxes («раскладка») |
| yt-dlp VOD | youtube-worker | YouTube / Kick / Twitch corpus |
| Pexels + Pixabay | WF-41 **inactive** | Stock hooks |
| Redis / embeddings | PC-03…PC-06 | Memory, semantic search |
| Cursor MCP (not n8n) | HeyGen, Higgsfield, ChatCut, Figma, Vercel | **needsAuth** in this agent |

n8n credential types present: `perplexityApi`, `openAiApi`, `anthropicApi`, `googlePalmApi` (Gemini), `googleDriveOAuth2Api`, SpyTrend basic, S3, SSH, Redis.

## How the industry actually does it (2026)

n8n does **not** edit video. It orchestrates a renderer ([Wireflow](https://www.wireflow.ai/blog/how-to-build-n8n-video-editing-workflows), [Shotstack](https://shotstack.io/learn/how-to-automate-shortform-videos/)). Three engines:

1. **Overlay + TTS on the same master** — fastest, what Factory v3/v5 already is.
2. **Template API** (Creatomate / Shotstack / Bannerbear / HyperFrames / Remotion) — JSON in, MP4 out, ~60–120s/clip in cloud.
3. **Generative reshoot** — only if the *shot* must change.

Self-hosted pattern that matches us: n8n + LLM JSON + TTS + ffmpeg matrix (`N` masters × `M` copy × `K` voices) ([AFFStudio](https://affstudio.org/2026/06/12/how-to-build-a-self-hosted-ai-video-factory-for-ad-creatives/)).

## Two-pass analysis (this is the missing product piece)

Perplexity + Gemini docs agree: do **not** ship a single “describe this video” prompt.

| Pass | Latency | Stack we can use | Output |
|------|---------|------------------|--------|
| Fast | 2–10s | ffprobe + scene cuts + layout URL (already in v3) | format, duration, coarse hook/CTA, “can we multiply?” |
| Deep | <2 min | Gemini **native video** (File API, already keyed on worker) + Whisper/ASR + OCR | beats with timestamps, spoken/on-screen CTA, overlay-safe rectangles, language |

Gemini 2.5 can take the MP4 directly (audio + frames, timestamps) ([Google AI](https://ai.google.dev/gemini-api/docs/video-understanding)). Default sample is 1 fps — fine for a 15–45s buyer ad; too sparse for a 2h VOD (keep dual-pipeline there).

Twelve Labs Pegasus: skip unless we need semantic search across thousands of ads. We already have embeddings + Redis.

## What to add / later / skip

**Must-have (on top of current stack)**

1. **Whisper / faster-whisper** on the worker — language detect, transcript, subtitle burn-in. Biggest gap vs Perplexity’s list (we have TTS out, almost no ASR in).
2. **Gemini native video** on `POST /jobs/buyer/multiply` deep pass — replace AD_B-scaled heuristic beats for buyer uploads.
3. **Compliance gate per GEO before export** — not a new SaaS; a JSON pack + hard fail. NL/PL cannot share the same “18+ and ship” path.
4. **Parallel TTS** (we already have OpenAI TTS) — Factory v5 splits batches; buyer path must fan-out, not serialize 22 geos.
5. **Meta Marketing API** (later-must for a *platform*) — pull winner stats so multiply starts from ads that actually spend, not a random MP4. SpyTrend covers *competitors*, not the buyer’s own account.

**TTS vendor:** keep **OpenAI TTS** as default (already in v3/v5/`tts-gen`). Add **ElevenLabs** only if a GEO’s voice quality is the reject reason. Google Chirp = fallback, not primary.

**Later**

- Creatomate or Shotstack as **overflow** if local ffmpeg queue backs up — do not replace `forge-renderer`.
- Deepgram if self-hosted Whisper becomes the bottleneck.
- HeyGen only if we sell presenter/UGC-face variants (`AD_STREAMER_PIP` / `AD_UGC` stubs).

**Skip as core path**

- Higgsfield / Kling / Runway for every multiply.
- Re-enabling Pexels/Pixabay for iGaming winners (compliance + brand drift).
- Celtra / Smartly (enterprise DCO; we already own the farm).

Cursor HeyGen/Higgsfield MCP: authenticate only when we explicitly build a “new hook” lane. Not needed for locale × CTA clones.

## SLA to promise on forge.vizioner.xyz

Perplexity’s buyer-facing split (do **not** put legal review in the same timer):

| Commitment | Target | Ours today |
|------------|--------|------------|
| Analysis plan | <10s | F6.1 probe+explode ~2s (heuristic) |
| First localized preview | <60s | Factory v3/v5 + renderer; often 30–60s / 1–2 geos |
| 20 GEO batch | 5–10 min parallel | Will miss if TTS/Drive stay serial |
| Compliance exceptions | best-effort, separate lane | Not gated |

Bottlenecks they name that we already feel: TTS, Drive fetch of the master, QC, human GEO copy. Layout cache in v3 is the right idea — keep it.

## Legal (hard gates, not copy tweaks)

- **NL:** untargeted gambling ads banned; digital ads must prove **≥95% of reached audience is 24+**; operator is liable for affiliates; no celebrity/influencer talent ([KSA leidraad Mar 2026](https://kansspelautoriteit.nl/sites/default/files/2026-03/Leidraad%20verbod%20op%20ongerichte%20reclame.pdf), [gamingcompliance.io](https://gamingcompliance.io/ksa-advertising-rules-in-the-netherlands-the-phased-restrictions-and-what-licence-holders-must-do-now/)). Forge listing NL as a default GEO is a product risk.
- **PL:** private online casino/slots advertising is not a normal affiliate lane; state-monopoly / betting-only ([Softswiss](https://www.softswiss.com/news/affiliate-marketing-trends-igaming-promotion-europe/)). Constructor `pl` pack stays placeholder.

Multiply should **block** NL/PL slot ads unless a human sets `compliance.allow = true` for a licensed operator brief.

## Recommended wiring (no new SaaS required for v1)

```
Forge upload
  → worker fast: ffprobe + layout (creative-localizer or forge-renderer /api/layout)
  → constructor explode (geo × CTA)           # already F6.1
  → n8n factory v5 webhook (parallel TTS + ffmpeg)
  → PC-26 Gemini QA sample
  → library + Drive
deep (async): Gemini native video + Whisper → rewrite beats / overlay_safe
```

HyperFrames `--batch` stays the *code-first* twin of ffmpeg overlays (F1.1), not a third cloud renderer.

## Ops note

`Perplexity Multi Gateway` currently embeds the Perplexity bearer token in a Code node. Move it to the existing `perplexityApi` / HTTP Header credential and rotate the key.
