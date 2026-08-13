Gitignored secret keys for the Creative Factory media connectors.

─── ПРОСТАЯ ИНСТРУКЦИЯ (RU) ───

Самый простой способ — один файл в корне проекта:

  .env

Открой его и вставь ключи ПОСЛЕ знака = (строки 8, 12, 15).
Файл уже создан, комментарии на русском.

Альтернатива — три отдельных файла (если не хочешь .env):

  library/_pipeline/secrets/HF_KEY.key
  library/_pipeline/secrets/PERPLEXITY_API_KEY.key
  library/_pipeline/secrets/FAL_KEY.key

В каждый — одна строка, только значение ключа (без кавычек).

Проверка:  bin/connect-factory --strict

─── EN ───

Priority (highest first):
1. Runtime secrets injected by Cursor Cloud Agent (HF_KEY, PERPLEXITY_API_KEY, FAL_KEY, …)
2. Repo .env or library/_pipeline/.env
3. Single-line files in this directory: <VAR_NAME>.key

Examples:
  bash bin/spytrend-register.sh   # auto OAuth client (free demo tier)
  cp HF_KEY.key.example HF_KEY.key
  cp PERPLEXITY_API_KEY.key.example PERPLEXITY_API_KEY.key
  cp FAL_KEY.key.example FAL_KEY.key

SpyTrend uses OAuth client_id/client_secret (not a static API key).
- Self-registered demo: SPYTREND_AUTH_METHOD=basic (default)
- Cabinet keys (spytrend.com/settings → AI): SPYTREND_AUTH_METHOD=post
After setup, Cursor MCP reads bin/spytrend-token.sh via headersHelper.

Verify wiring:
  bin/connect-factory
