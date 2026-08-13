Gitignored secret keys for the Creative Factory media connectors.

Priority (highest first):
1. Runtime secrets injected by Cursor Cloud Agent (HF_KEY, PERPLEXITY_API_KEY, FAL_KEY, …)
2. Repo .env or library/_pipeline/.env
3. Single-line files in this directory: <VAR_NAME>.key

Examples:
  cp HF_KEY.key.example HF_KEY.key
  cp PERPLEXITY_API_KEY.key.example PERPLEXITY_API_KEY.key
  cp FAL_KEY.key.example FAL_KEY.key

Verify wiring:
  bin/connect-factory
