# Куда класть ключи (Hetzner)

**Не в git. Не в чат. Не в n8n Code node (`jsCode`).**

Живые файлы на `root@65.108.48.54`. После правки `.env` перезапусти соответствующий compose. Значения ниже — **имена переменных и формат**, не сами секреты.

```
KEY=value
```

Одна пара на строку. Без `export`. Кавычки только если в значении есть пробелы. Без пробелов вокруг `=`.

---

## 1. Worker (youtube-worker) — файл

**Путь:** `/opt/igaming-library/_pipeline/deploy/.env`  
**Compose:** `env_file: .env` в `docker-compose.yml`  
**После правки:** `cd /opt/igaming-library/_pipeline/deploy && docker compose up -d`

| Переменная | Зачем | Вид |
|------------|--------|-----|
| `CAPTURE_API_TOKEN` | Bearer на `POST /jobs/buyer/multiply` и VOD jobs | длинная случайная строка, **без** слова `Bearer` |
| `LIBRARY_HOST_PATH` | bind-mount библиотеки | абсолютный путь хоста, сейчас `/opt/igaming-library` |
| `PORT` | проброс `127.0.0.1:PORT` | `8787` |

Опционально (перекрывает файл ключа):

```
GEMINI_API_KEY=AIza...   # сырой ключ Google AI Studio, без Bearer
```

`CAPTURE_API_TOKEN` и Forge `WORKER_TOKEN` — **одно и то же значение**.

Порт `8787` наружу не открывать.

---

## 2. Forge (forge.vizioner.xyz) — файл

**Путь:** `/opt/forge/.env`  
**Compose:** `/opt/forge/compose.yml` читает эти имена  
**После правки:** `cd /opt/forge && docker compose -f compose.yml up -d`

| Переменная | В контейнере становится | Вид |
|------------|-------------------------|-----|
| `FORGE_DATABASE_URL` | `DATABASE_URL` | `postgres://user:pass@host:5432/db` |
| `FORGE_ADMIN_EMAIL` | `ADMIN_EMAIL` | email |
| `FORGE_ADMIN_PASSWORD` | `ADMIN_PASSWORD` | пароль админки |
| `FORGE_N8N_FACTORY_KEY` | `N8N_FACTORY_KEY` | то же значение, что у n8n credential `HTTP Header Auth (x-agent-os-key)` |
| `WORKER_URL` | `WORKER_URL` | `http://youtube-worker:8787` (docker DNS) |
| `WORKER_TOKEN` | `WORKER_TOKEN` | = `CAPTURE_API_TOKEN` |

Forge шлёт на n8n заголовок **строго** `x-agent-os-key` (строчными).

---

## 3. Gemini (воркер / dual analysis) — файл на одну строку

**Путь:** `/opt/igaming-library/_pipeline/secrets/gemini.key`  
**В контейнере:** `/data/library/_pipeline/secrets/gemini.key`  
**Права:** `chmod 600`

Формат:

```
<сырой ключ одной строкой>
```

- Без `#`-комментариев в этом файле (комментарии код пропускает, но живой README просит их убрать).
- Без кавычек, без `Bearer`, без `key=`.
- Взять: https://aistudio.google.com/apikey
- Пример-заглушка: `library/_pipeline/secrets/gemini.key.example`

Код читает сначала `GEMINI_API_KEY`, иначе первую непустую не-комментарную строку файла.

---

## 4. YouTube / Kick / Twitch cookies — Netscape-файл

**Путь:** `/opt/igaming-library/_pipeline/secrets/youtube.cookies.txt`  
**Env:** `YTDLP_COOKIES` (по умолчанию тот же путь внутри контейнера)

Первая строка должна быть:

```
# Netscape HTTP Cookie File
```

Дальше обычный `cookies.txt` (колонки: domain, flag, path, secure, expiry, name, value). Экспорт из браузера расширением «Get cookies.txt LOCALLY» / аналог. `chmod 600`.

---

## 5. n8n SaaS-ключи — только Credentials в UI

**Где:** https://n8n.vizioner.xyz → **Credentials** (шифруются `N8N_ENCRYPTION_KEY` из `/opt/video-factory/.env`).

`N8N_BLOCK_ENV_ACCESS_IN_NODE=true` — Code node **не видит** `process.env` / `$env`. Поэтому ключ в `jsCode` — поломка, не «быстрый фикс».

| Credential (уже есть) | Тип | Куда вставлять ключ |
|-----------------------|-----|---------------------|
| `Perplexity account` | `perplexityApi` | поле API Key = `pplx-...` **без** `Bearer` |
| `Perplexity API` | `httpHeaderAuth` | Name `Authorization`, Value `Bearer pplx-...` |
| `OpenAI (adspend account)` | `openAiApi` | официальное поле API key (`sk-...`) |
| `Google Gemini(PaLM) Api account` | `googlePalmApi` | API key Google AI |
| `Gemini Vision API Key` | `httpQueryAuth` | query name `key`, value = сырой Gemini-ключ |
| `HTTP Header Auth (x-agent-os-key)` | `httpHeaderAuth` | Name `x-agent-os-key`, Value = тот же секрет, что `FORGE_N8N_FACTORY_KEY` |
| `Google Drive account` | OAuth2 | через UI Google, не файлом |
| `SpyTrend MCP` | `httpBasicAuth` | user/pass из кабинета SpyTrend |
| `Anthropic account` | `anthropicApi` | только если воркфлоу реально зовёт Claude |

Webhook фабрики: `https://n8n.vizioner.xyz/webhook/prod-run-7a7298` + заголовок `x-agent-os-key`.

**Perplexity Multi Gateway (`pplx-multi-qa`):** сейчас ключ зашит в Code node. Перенести на `Perplexity account` (HTTP Request), **ротировать** старый `pplx-...`.

---

## 6. Не сюда

| Что | Куда на самом деле |
|-----|-------------------|
| HeyGen / Higgsfield / ChatCut / Figma MCP | настройки MCP в Cursor, не Hetzner, пока нет «new hook»-lane |
| `OPENAI_API_KEY` / `HIGGSFIELD_API_KEY` в `/opt/creative-factory/.env` | Hermes MVP, не buyer multiply |
| ElevenLabs (если понадобится) | n8n HTTP Header `xi-api-key`, не worker `.env` |
| Meta Marketing API | n8n OAuth, не файл в `secrets/` |
| Whisper local | ключ не нужен |

---

## Чеклист после вставки

1. Файл сохранился, `chmod 600` на ключи и cookies.
2. `git status` в этом репо **не** показывает `.env` / `gemini.key` / cookies.
3. Worker: `curl -sS -H "Authorization: Bearer $CAPTURE_API_TOKEN" http://127.0.0.1:8787/health`
4. Forge видит воркер по `WORKER_URL` из своей сети (`youtube-worker:8787`).
5. n8n: тестовый узел с credential, не с ключом в коде.

Когда ключ на месте — достаточно написать агенту «ключ готов», **не присылая сам ключ**.
