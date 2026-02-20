SHELL := /bin/bash

COMPOSE_FILE ?= docker-compose.dev.yml
COMPOSE := docker compose -f $(COMPOSE_FILE)

.PHONY: auth-qr up logs

auth-qr:
	@$(COMPOSE) stop app
	@rm -f sessions/user_session.session
	@$(COMPOSE) run --rm -it app python -c 'import os,sys,subprocess,traceback,inspect;from telethon import TelegramClient;code="try:\n import qrcode\nexcept Exception:\n subprocess.check_call([sys.executable,\"-m\",\"pip\",\"install\",\"--no-cache-dir\",\"qrcode\"])\n import qrcode\nc=TelegramClient(os.environ.get(\"TELETHON_SESSION_NAME\",\"/app/sessions/user_session\"),int(os.environ[\"TG_API_ID\"]),os.environ[\"TG_API_HASH\"])\ntry:\n c.loop.run_until_complete(c.connect()); q=c.loop.run_until_complete(c.qr_login()); print(\"QR_URL:\",q.url); qr=qrcode.QRCode(border=1); qr.add_data(q.url); qr.make(fit=True); qr.print_ascii(invert=True); print(\"Scan in Telegram mobile: Settings -> Devices -> Link Desktop Device\"); c.loop.run_until_complete(q.wait(timeout=300)); print(\"Session saved\")\nexcept Exception as e:\n print(\"QR_LOGIN_ERROR:\",type(e).__name__,e); traceback.print_exc()\nfinally:\n try:\n  r=c.disconnect();\n  if inspect.isawaitable(r): c.loop.run_until_complete(r)\n except Exception as e:\n  print(\"DISCONNECT_ERROR:\",type(e).__name__,e)";exec(code)'

up:
	@$(COMPOSE) up -d

logs:
	@$(COMPOSE) logs -f app
