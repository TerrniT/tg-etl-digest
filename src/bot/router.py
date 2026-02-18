# FILE: src/bot/router.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Compose aiogram router bindings for command and FSM handlers.
#   SCOPE: Register command filters and wire runtime dependencies into handler call closures.
#   DEPENDS: M-BOT-HANDLERS, M-BOT-STATES, M-CONFIG, M-SUMMARIZER-LLM
#   LINKS: docs/development-plan.xml#M-BOT-ROUTER, docs/knowledge-graph.xml#M-BOT-ROUTER
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   build_router — Build Router and bind command/state handlers with shared dependencies.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE contracts and semantic block markers.
# END_CHANGE_SUMMARY

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


# START_CONTRACT: build_router
#   PURPOSE: Register all command/state handlers and return composed aiogram Router.
#   INPUTS: { pool: asyncpg.Pool, tg_client: TelegramClient, summarizer: Summarizer, cfg: Config }
#   OUTPUTS: { Router - configured bot router }
#   SIDE_EFFECTS: defines closure handlers bound with runtime dependencies
#   LINKS: M-BOT-ROUTER, M-BOT-HANDLERS
# END_CONTRACT: build_router
def build_router(pool, tg_client, summarizer: Summarizer, cfg: Config) -> Router:
    # START_BLOCK_CREATE_ROUTER_INSTANCE
    router = Router()
    # END_BLOCK_CREATE_ROUTER_INSTANCE

    # START_BLOCK_REGISTER_COMMAND_HANDLERS
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
    # END_BLOCK_REGISTER_COMMAND_HANDLERS

    return router
