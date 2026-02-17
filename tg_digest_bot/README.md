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

## Migrations
Run SQL from `migrations/001_init.sql` against your PostgreSQL database.
