import asyncio

from aiogram import Bot, Dispatcher

from src.app.config import load_config
from src.app.logging import setup_logging
from src.bot.router import build_router
from src.extractor.telethon_client import create_telethon_client
from src.storage.postgres import create_pool
from src.summarizer.llm import Summarizer


async def main() -> None:
    setup_logging()
    cfg = load_config()

    pool = await create_pool(cfg.database_url)
    tg_client = await create_telethon_client(cfg.telethon_session_name, cfg.tg_api_id, cfg.tg_api_hash)
    summarizer = Summarizer(api_key=cfg.openai_api_key, model=cfg.openai_model)

    bot = Bot(token=cfg.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(build_router(pool=pool, tg_client=tg_client, summarizer=summarizer, cfg=cfg))

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
