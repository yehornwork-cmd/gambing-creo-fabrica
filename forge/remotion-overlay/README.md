# Remotion overlay — тот же креатив, что рисует forge-renderer

Композиция `Overlay`: мастер 9×16, две строки заголовка, чёрные плашки, стор-бейджи, дисклеймер, опциональный VO. Геометрия скопирована из `forge/renderer/server.mjs` (`layoutFor` + `compositionHtml`), чтобы Lambda и локальный HyperFrames давали один кадр.

## Пропсы (как `POST /api/render`)

| Поле | Смысл |
|---|---|
| `masterSrc` | URL мастера |
| `voSrc` | URL озвучки (пусто = без голоса, мастер muted) |
| `headline` | ровно 2 строки |
| `disclaimer` | нижняя строка |
| `badgeAppleSrc` / `badgeGoogleSrc` | PNG бейджей |
| `durationInSeconds` | длина ролика |
| `headlineBox` | `{x,y,w,h}` из `/api/layout`; иначе дефолт 1080×1920 |

Пример: `props.example.json`.

## Локально

```bash
cd forge/remotion-overlay
npm install
npm run test:layout
npx remotion compositions
npx remotion render Overlay out/overlay.mp4 --props=props.example.json
```

Studio: `npm run studio`. Без `masterSrc` — чёрный фон и тексты.

## 100 роликов за раз

Это не `remotion render` на одной машине. Дальше:

1. `npx remotion lambda sites create` + `npx remotion lambda functions deploy`
2. На каждый гео: `npx remotion lambda render <serve-url> Overlay --props=geo.json` (параллельно)
3. n8n только кладёт 100 пропсов в очередь и забирает URL из S3

Один 15-секундный ролик на Lambda — десятки секунд wall-clock; сотня заказов едет одновременно, не 100 Chromium на Hetzner.
