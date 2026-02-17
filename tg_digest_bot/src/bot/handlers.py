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


def format_add_response(resp: AddChannelsResponse) -> str:
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

    if not lines:
        return "Нечего добавлять. Пример: /add @channel1 https://t.me/channel2"

    return "\n".join(lines).strip()


async def handle_start(message: types.Message) -> None:
    await message.answer("Привет! Добавь каналы через /add, потом запусти /analytic для дайджеста.")


async def handle_add(message: types.Message, state: FSMContext, pool, cfg: Config) -> None:
    try:
        text = message.text or ""
        parts = text.split(maxsplit=1)
        args = parts[1].strip() if len(parts) > 1 else ""

        if not args:
            await state.set_state(AddChannelsFSM.WAITING_CHANNELS_INPUT)
            await message.answer(
                "Пришли список каналов одним сообщением.\n"
                "Примеры:\n"
                "• @channel1 @channel2\n"
                "• https://t.me/channel1 https://t.me/channel2"
            )
            return

        resp = await add_channels_usecase(
            pool,
            message.from_user.id,
            args,
            max_add_per_call=cfg.max_add_per_call,
            max_per_user=cfg.max_channels_per_user,
        )
        await message.answer(format_add_response(resp))
    except DomainError:
        await message.answer("Не удалось добавить каналы. Попробуйте позже.")


async def handle_add_waiting_input(message: types.Message, state: FSMContext, pool, cfg: Config) -> None:
    try:
        raw = (message.text or "").strip()
        if not raw:
            await message.answer("Пусто. Пример: @channel1 https://t.me/channel2")
            return

        resp = await add_channels_usecase(
            pool,
            message.from_user.id,
            raw,
            max_add_per_call=cfg.max_add_per_call,
            max_per_user=cfg.max_channels_per_user,
        )
        await message.answer(format_add_response(resp))

        parsed = parse_channels(raw, max_items=cfg.max_add_per_call)
        if parsed.valid_handles:
            await state.clear()
    except DomainError:
        await message.answer("Не удалось добавить каналы. Попробуйте позже.")


async def handle_list(message: types.Message, pool) -> None:
    try:
        channels = await list_user_channels(pool, message.from_user.id)
        if not channels:
            await message.answer("Список каналов пуст. Добавьте через /add")
            return

        lines = ["Ваши каналы:"] + [f"• https://t.me/{str(h)}" for h in channels]
        await message.answer("\n".join(lines))
    except DomainError:
        await message.answer("Не удалось получить список каналов.")


async def handle_remove(message: types.Message, pool) -> None:
    try:
        text = message.text or ""
        parts = text.split(maxsplit=1)
        args = parts[1].strip() if len(parts) > 1 else ""
        if not args:
            await message.answer("Использование: /remove @channel")
            return

        parsed = parse_channels(args, max_items=1)
        if not parsed.valid_handles:
            await message.answer("Не смог распознать канал. Использование: /remove @channel")
            return

        handle = parsed.valid_handles[0]
        removed = await remove_channel_for_user(pool, message.from_user.id, handle)
        if removed:
            await message.answer(f"Удалено: https://t.me/{str(handle)}")
        else:
            await message.answer(f"Канал не найден в вашем списке: https://t.me/{str(handle)}")
    except DomainError:
        await message.answer("Не удалось удалить канал.")


async def handle_analytic(message: types.Message, pool, tg_client, summarizer: Summarizer, cfg: Config) -> None:
    try:
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

        for chunk in resp.chunks:
            await message.answer(chunk)
    except DomainError:
        await message.answer("Не удалось собрать дайджест. Попробуйте позже.")
