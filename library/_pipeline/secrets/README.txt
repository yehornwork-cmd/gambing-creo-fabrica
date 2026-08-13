GEMINI: gemini.key — одна строка, не коммитить.
YT-DLP: youtube.cookies.txt — Netscape cookies.txt, не коммитить.
Полный runbook: library/_pipeline/SECRETS.md

Путь в контейнере: /data/library/_pipeline/secrets/youtube.cookies.txt
Env: YTDLP_COOKIES или YOUTUBE_COOKIES (иначе этот файл).

1. Открой gemini.key (в этой же папке)
2. Удали комментарии (# ...)
3. Вставь ключ одной строкой
4. Сохрани
5. Напиши агенту: «ключ готов» (сам ключ в чат не слать)

Ключ НЕ коммитится в git.
Получить ключ: https://aistudio.google.com/apikey
