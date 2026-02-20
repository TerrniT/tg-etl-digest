# FILE: src/bot/handlers.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Implement Telegram command handlers and user-facing response formatting.
#   SCOPE: Handle /start, /add, /list, /remove, /analytic flows with FSM transitions and domain error mapping.
#   DEPENDS: M-CONFIG, M-ERRORS, M-PARSING-CHANNELS, M-SVC-ADD-CHANNELS, M-SVC-ANALYTIC, M-STORAGE-REPO, M-SUMMARIZER-LLM, M-BOT-STATES
#   LINKS: docs/development-plan.xml#M-BOT-HANDLERS, docs/knowledge-graph.xml#M-BOT-HANDLERS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   format_add_response — Render grouped add-channels outcome.
#   handle_start — Send onboarding message.
#   handle_add — Process /add command (inline args or FSM transition).
#   handle_add_waiting_input — Process add flow continuation in FSM state.
#   handle_list — List stored channels for user.
#   handle_remove — Remove one channel from user list.
#   handle_analytic — Run analytic use case and send chunked digest.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.1.0 - Added error-level logging for handled domain failures.
# END_CHANGE_SUMMARY

import logging

from aiogram import types
from aiogram.fsm.context import FSMContext

from src.app.config import Config
from src.app.errors import DomainError
from src.parsing.channels import parse_channels
from src.services.add_channels import AddChannelsResponse, add_channels_usecase
from src.services.analytic import analytic_usecase
from src.storage.repository import list_user_channels, remove_channel_for_user
from src.summarizer.llm import Summarizer

from .states import AddChannelsFSM

logger = logging.getLogger(__name__)


# START_CONTRACT: format_add_response
#   PURPOSE: Convert AddChannelsResponse buckets to human-readable Telegram text.
#   INPUTS: { resp: AddChannelsResponse }
#   OUTPUTS: { str - formatted message body }
#   SIDE_EFFECTS: none
#   LINKS: M-BOT-HANDLERS, M-SVC-ADD-CHANNELS
# END_CONTRACT: format_add_response
def format_add_response(resp: AddChannelsResponse) -> str:
    # START_BLOCK_ACCUMULATE_RESPONSE_SECTIONS
    lines: list[str] = []

    if resp.added:
        lines.append(f"✅ Добавлено ({len(resp.added)}):")
        lines.extend([f"• https://t.me/{str(h)}" for h in resp.added])
        lines.append("")

    if resp.already_present:
        lines.append(f"⚠️ Уже было ({len(resp.already_present)}):")
        lines.extend([f"• https://t.me/{str(h)}" for h in resp.already_present])
        lines.append("")

    if resp.rejected_due_to_limit:
        lines.append(f"⛔ Превышен лимит, не добавил ({len(resp.rejected_due_to_limit)}):")
        lines.extend([f"• https://t.me/{str(h)}" for h in resp.rejected_due_to_limit])
        lines.append("")

    if resp.truncated_tokens:
        lines.append(f"… Лимит за один раз, пропустил ({len(resp.truncated_tokens)}):")
        lines.extend([f"• {t}" for t in resp.truncated_tokens])
        lines.append("")

    if resp.invalid_tokens:
        lines.append(f"❌ Не распознано ({len(resp.invalid_tokens)}):")
        lines.extend([f"• {t}" for t in resp.invalid_tokens])
        lines.append("")
    # END_BLOCK_ACCUMULATE_RESPONSE_SECTIONS

    # START_BLOCK_RETURN_FINAL_ADD_MESSAGE
    if not lines:
        return "Нечего добавлять. Пример: /add @channel1 https://t.me/channel2"

    return "\n".join(lines).strip()
    # END_BLOCK_RETURN_FINAL_ADD_MESSAGE


# START_CONTRACT: handle_start
#   PURPOSE: Send basic onboarding instructions.
#   INPUTS: { message: aiogram.types.Message }
#   OUTPUTS: { None }
#   SIDE_EFFECTS: sends Telegram message
#   LINKS: M-BOT-HANDLERS
# END_CONTRACT: handle_start
async def handle_start(message: types.Message) -> None:
    await message.answer("Привет! Добавь каналы через /add, потом запусти /analytic для дайджеста.")


# START_CONTRACT: handle_add
#   PURPOSE: Handle /add command with optional inline arguments and FSM fallback.
#   INPUTS: { message: Message, state: FSMContext, pool: asyncpg.Pool, cfg: Config }
#   OUTPUTS: { None }
#   SIDE_EFFECTS: writes FSM state and sends Telegram messages
#   LINKS: M-BOT-HANDLERS, M-SVC-ADD-CHANNELS, M-BOT-STATES
# END_CONTRACT: handle_add
async def handle_add(message: types.Message, state: FSMContext, pool, cfg: Config) -> None:
    try:
        # START_BLOCK_PARSE_ADD_COMMAND_ARGS
        text = message.text or ""
        parts = text.split(maxsplit=1)
        args = parts[1].strip() if len(parts) > 1 else ""
        # END_BLOCK_PARSE_ADD_COMMAND_ARGS

        # START_BLOCK_HANDLE_EMPTY_ADD_ARGS_WITH_FSM
        if not args:
            await state.set_state(AddChannelsFSM.WAITING_CHANNELS_INPUT)
            await message.answer(
                "Пришли список каналов одним сообщением.\n"
                "Примеры:\n"
                "• @channel1 @channel2\n"
                "• https://t.me/channel1 https://t.me/channel2"
            )
            return
        # END_BLOCK_HANDLE_EMPTY_ADD_ARGS_WITH_FSM

        # START_BLOCK_EXECUTE_ADD_USECASE_AND_REPLY
        resp = await add_channels_usecase(
            pool,
            message.from_user.id,
            args,
            max_add_per_call=cfg.max_add_per_call,
            max_per_user=cfg.max_channels_per_user,
        )
        await message.answer(format_add_response(resp))
        # END_BLOCK_EXECUTE_ADD_USECASE_AND_REPLY
    except DomainError:
        logger.exception("[BotHandlers][handle_add][DOMAIN_ERROR] failed to process /add command")
        await message.answer("Не удалось добавить каналы. Попробуйте позже.")


# START_CONTRACT: handle_add_waiting_input
#   PURPOSE: Handle follow-up add payload when user is in WAITING_CHANNELS_INPUT state.
#   INPUTS: { message: Message, state: FSMContext, pool: asyncpg.Pool, cfg: Config }
#   OUTPUTS: { None }
#   SIDE_EFFECTS: clears FSM state on successful parsed input and sends Telegram messages
#   LINKS: M-BOT-HANDLERS, M-SVC-ADD-CHANNELS, M-PARSING-CHANNELS, M-BOT-STATES
# END_CONTRACT: handle_add_waiting_input
async def handle_add_waiting_input(message: types.Message, state: FSMContext, pool, cfg: Config) -> None:
    try:
        # START_BLOCK_VALIDATE_WAITING_INPUT_PAYLOAD
        raw = (message.text or "").strip()
        if not raw:
            await message.answer("Пусто. Пример: @channel1 https://t.me/channel2")
            return
        # END_BLOCK_VALIDATE_WAITING_INPUT_PAYLOAD

        # START_BLOCK_RUN_ADD_USECASE_AND_REPLY
        resp = await add_channels_usecase(
            pool,
            message.from_user.id,
            raw,
            max_add_per_call=cfg.max_add_per_call,
            max_per_user=cfg.max_channels_per_user,
        )
        await message.answer(format_add_response(resp))
        # END_BLOCK_RUN_ADD_USECASE_AND_REPLY

        # START_BLOCK_CLEAR_FSM_STATE_ON_VALID_PARSED_HANDLES
        parsed = parse_channels(raw, max_items=cfg.max_add_per_call)
        if parsed.valid_handles:
            await state.clear()
        # END_BLOCK_CLEAR_FSM_STATE_ON_VALID_PARSED_HANDLES
    except DomainError:
        logger.exception(
            "[BotHandlers][handle_add_waiting_input][DOMAIN_ERROR] failed to process FSM payload"
        )
        await message.answer("Не удалось добавить каналы. Попробуйте позже.")


# START_CONTRACT: handle_list
#   PURPOSE: Return list of saved channels for the requesting user.
#   INPUTS: { message: Message, pool: asyncpg.Pool }
#   OUTPUTS: { None }
#   SIDE_EFFECTS: sends Telegram messages
#   LINKS: M-BOT-HANDLERS, M-STORAGE-REPO
# END_CONTRACT: handle_list
async def handle_list(message: types.Message, pool) -> None:
    try:
        # START_BLOCK_LOAD_AND_VALIDATE_CHANNEL_LIST
        channels = await list_user_channels(pool, message.from_user.id)
        if not channels:
            await message.answer("Список каналов пуст. Добавьте через /add")
            return
        # END_BLOCK_LOAD_AND_VALIDATE_CHANNEL_LIST

        # START_BLOCK_RENDER_CHANNEL_LIST_MESSAGE
        lines = ["Ваши каналы:"] + [f"• https://t.me/{str(h)}" for h in channels]
        await message.answer("\n".join(lines))
        # END_BLOCK_RENDER_CHANNEL_LIST_MESSAGE
    except DomainError:
        logger.exception("[BotHandlers][handle_list][DOMAIN_ERROR] failed to list user channels")
        await message.answer("Не удалось получить список каналов.")


# START_CONTRACT: handle_remove
#   PURPOSE: Remove one parsed channel handle from the requesting user's saved list.
#   INPUTS: { message: Message, pool: asyncpg.Pool }
#   OUTPUTS: { None }
#   SIDE_EFFECTS: deletes storage relation and sends Telegram messages
#   LINKS: M-BOT-HANDLERS, M-PARSING-CHANNELS, M-STORAGE-REPO
# END_CONTRACT: handle_remove
async def handle_remove(message: types.Message, pool) -> None:
    try:
        # START_BLOCK_PARSE_REMOVE_COMMAND_ARGS
        text = message.text or ""
        parts = text.split(maxsplit=1)
        args = parts[1].strip() if len(parts) > 1 else ""
        if not args:
            await message.answer("Использование: /remove @channel")
            return
        # END_BLOCK_PARSE_REMOVE_COMMAND_ARGS

        # START_BLOCK_VALIDATE_REMOVE_HANDLE
        parsed = parse_channels(args, max_items=1)
        if not parsed.valid_handles:
            await message.answer("Не смог распознать канал. Использование: /remove @channel")
            return
        # END_BLOCK_VALIDATE_REMOVE_HANDLE

        # START_BLOCK_EXECUTE_REMOVE_AND_REPLY
        handle = parsed.valid_handles[0]
        removed = await remove_channel_for_user(pool, message.from_user.id, handle)
        if removed:
            await message.answer(f"Удалено: https://t.me/{str(handle)}")
        else:
            await message.answer(f"Канал не найден в вашем списке: https://t.me/{str(handle)}")
        # END_BLOCK_EXECUTE_REMOVE_AND_REPLY
    except DomainError:
        logger.exception("[BotHandlers][handle_remove][DOMAIN_ERROR] failed to remove channel")
        await message.answer("Не удалось удалить канал.")


# START_CONTRACT: handle_analytic
#   PURPOSE: Run analytic use case and deliver digest chunks to user.
#   INPUTS: { message: Message, pool: asyncpg.Pool, tg_client: TelegramClient, summarizer: Summarizer, cfg: Config }
#   OUTPUTS: { None }
#   SIDE_EFFECTS: triggers ETL + LLM calls and sends one or more Telegram messages
#   LINKS: M-BOT-HANDLERS, M-SVC-ANALYTIC
# END_CONTRACT: handle_analytic
async def handle_analytic(message: types.Message, pool, tg_client, summarizer: Summarizer, cfg: Config) -> None:
    try:
        # START_BLOCK_NOTIFY_USER_AND_RUN_ANALYTIC_USECASE
        await message.answer("Собираю посты и делаю дайджест…")
        resp = await analytic_usecase(
            pool=pool,
            tg_user_id=message.from_user.id,
            tg_client=tg_client,
            summarizer=summarizer,
            posts_per_channel=cfg.posts_per_channel,
            max_channels_per_call=cfg.max_channels_per_analytic_call,
            max_chars_per_post=cfg.max_chars_per_post,
            tg_message_max_len=cfg.tg_message_max_len,
            include_post_links=cfg.include_post_links,
        )
        # END_BLOCK_NOTIFY_USER_AND_RUN_ANALYTIC_USECASE

        # START_BLOCK_SEND_DIGEST_CHUNKS
        for chunk in resp.chunks:
            await message.answer(chunk)
        # END_BLOCK_SEND_DIGEST_CHUNKS
    except DomainError:
        logger.exception("[BotHandlers][handle_analytic][DOMAIN_ERROR] failed to build analytic digest")
        await message.answer("Не удалось собрать дайджест. Попробуйте позже.")
