from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.app.config import Config
from src.summarizer.llm import Summarizer

from .handlers import (
    handle_add,
    handle_add_waiting_input,
    handle_analytic,
    handle_list,
    handle_remove,
    handle_start,
)
from .states import AddChannelsFSM


def build_router(pool, tg_client, summarizer: Summarizer, cfg: Config) -> Router:
    router = Router()

    @router.message(Command("start"))
    async def _start(message: types.Message) -> None:
        await handle_start(message)

    @router.message(Command("add"))
    async def _add(message: types.Message, state: FSMContext) -> None:
        await handle_add(message, state, pool, cfg)

    @router.message(AddChannelsFSM.WAITING_CHANNELS_INPUT)
    async def _add_waiting(message: types.Message, state: FSMContext) -> None:
        await handle_add_waiting_input(message, state, pool, cfg)

    @router.message(Command("list"))
    async def _list(message: types.Message) -> None:
        await handle_list(message, pool)

    @router.message(Command("remove"))
    async def _remove(message: types.Message) -> None:
        await handle_remove(message, pool)

    @router.message(Command("analytic"))
    async def _analytic(message: types.Message) -> None:
        await handle_analytic(message, pool, tg_client, summarizer, cfg)

    return router
