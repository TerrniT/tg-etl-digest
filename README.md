# TG Digest Bot

Telegram bot that stores user-defined list of channels and generates `/analytic` digest:
- summary of last 5 text posts per channel
- channel links and optional post links

## Requirements
- Python 3.11+
- Postgres
- Telegram Bot token
- Telethon user session (MTProto) credentials

## Commands
- /start
- /add
- /list
- /remove
- /analytic

## Environment
See `.env.example`.

## Run
```bash
python -m src.app.main
```

## Run with Docker Compose
1. Fill required variables in `.env`:
   - `BOT_TOKEN`
   - `TG_API_ID`
   - `TG_API_HASH`
   - `AI_API_KEY`
   - `AI_BASE_URL`
2. Run one-time Telethon QR auth to create MTProto session file:
```bash
make auth-qr
```
This command prints an ASCII QR in terminal, waits for confirmation, and stores the session in local `sessions/` directory.
3. Start stack (app + postgres):
```bash
docker compose -f docker-compose.dev.yml up --build -d
# or: make up
```
4. Check logs:
```bash
docker compose -f docker-compose.dev.yml logs -f app
# or: make logs
```

## Migrations
Run SQL from `migrations/001_init.sql` against your PostgreSQL database.
