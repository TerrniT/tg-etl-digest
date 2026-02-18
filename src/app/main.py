# FILE: src/app/main.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Bootstrap runtime dependencies and start aiogram polling loop.
#   SCOPE: Configure logging, load config, initialize infra clients, compose router, and launch dispatcher.
#   DEPENDS: M-APP-LOGGING, M-CONFIG, M-STORAGE-POOL, M-TELETHON-CLIENT, M-SUMMARIZER-LLM, M-BOT-ROUTER
#   LINKS: docs/development-plan.xml#M-ENTRY-APP, docs/knowledge-graph.xml#M-ENTRY-APP
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   main — Async application bootstrap entrypoint.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE contracts and semantic block markers.
# END_CHANGE_SUMMARY

import asyncio

from aiogram import Bot, Dispatcher

from src.app.config import load_config
from src.app.logging import setup_logging
from src.bot.router import build_router
from src.extractor.telethon_client import create_telethon_client
from src.storage.postgres import create_pool
from src.summarizer.llm import Summarizer


# START_CONTRACT: main
#   PURPOSE: Initialize all runtime dependencies and start Telegram bot polling.
#   INPUTS: {}
#   OUTPUTS: { None }
#   SIDE_EFFECTS: opens DB connections, starts Telethon session, initializes bot polling loop
#   LINKS: M-ENTRY-APP, M-CONFIG, M-STORAGE-POOL, M-TELETHON-CLIENT, M-SUMMARIZER-LLM, M-BOT-ROUTER
# END_CONTRACT: main
async def main() -> None:
    # START_BLOCK_INIT_CONFIG_AND_LOGGING
    setup_logging()
    cfg = load_config()
    # END_BLOCK_INIT_CONFIG_AND_LOGGING

    # START_BLOCK_INIT_INFRA_CLIENTS
    pool = await create_pool(cfg.database_url)
    tg_client = await create_telethon_client(cfg.telethon_session_name, cfg.tg_api_id, cfg.tg_api_hash)
    summarizer = Summarizer(api_key=cfg.openai_api_key, model=cfg.openai_model)
    # END_BLOCK_INIT_INFRA_CLIENTS

    # START_BLOCK_COMPOSE_ROUTER_AND_START_POLLING
    bot = Bot(token=cfg.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(build_router(pool=pool, tg_client=tg_client, summarizer=summarizer, cfg=cfg))

    await dispatcher.start_polling(bot)
    # END_BLOCK_COMPOSE_ROUTER_AND_START_POLLING


if __name__ == "__main__":
    asyncio.run(main())
