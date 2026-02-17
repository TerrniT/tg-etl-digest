from dataclasses import dataclass
from datetime import datetime, timezone

from telethon import TelegramClient

from src.app.errors import ExtractError, SummarizeError
from src.digest.assembler import assemble_digest
from src.digest.chunking import chunk_text_for_telegram
from src.domain.dto import ChannelSummaryDTO, DigestDTO
from src.extractor.telethon_extractor import fetch_last_posts
from src.storage.repository import list_user_channels
from src.summarizer.llm import Summarizer
from src.transform.posts import transform_posts


@dataclass(frozen=True)
class AnalyticResponse:
    digest: DigestDTO
    chunks: list[str]
    warning: str | None


async def analytic_usecase(
    pool,
    tg_user_id: int,
    tg_client: TelegramClient,
    summarizer: Summarizer,
    *,
    posts_per_channel: int,
    max_channels_per_call: int,
    max_chars_per_post: int,
    tg_message_max_len: int,
    include_post_links: bool,
) -> AnalyticResponse:
    handles = await list_user_channels(pool, tg_user_id)
    total = len(handles)
    warning = None

    if total == 0:
        digest = assemble_digest(
            tg_user_id=tg_user_id,
            channel_summaries=[],
            created_at=datetime.now(timezone.utc),
            include_post_links=include_post_links,
        )
        return AnalyticResponse(digest=digest, chunks=["Сначала добавь каналы через /add."], warning=None)

    if total > max_channels_per_call:
        warning = f"Обработал первые {max_channels_per_call} каналов из {total}, чтобы не превышать лимиты."
        handles = handles[:max_channels_per_call]

    summaries: list[ChannelSummaryDTO] = []

    for handle in handles:
        channel_link = f"https://t.me/{str(handle)}"
        posts = []

        try:
            posts = await fetch_last_posts(tg_client, handle, limit=posts_per_channel)
            posts = transform_posts(posts, max_chars_per_post=max_chars_per_post)

            if not posts:
                summaries.append(
                    ChannelSummaryDTO(
                        channel_handle=handle,
                        channel_link=channel_link,
                        summary_text="Нет текстовых постов среди последних сообщений.",
                        post_links=[],
                    )
                )
                continue

            summary_text = await summarizer.summarize_channel(handle, channel_link, posts)
            post_links = [p.permalink for p in posts if p.permalink] if include_post_links else []
            summaries.append(
                ChannelSummaryDTO(
                    channel_handle=handle,
                    channel_link=channel_link,
                    summary_text=summary_text,
                    post_links=post_links,
                )
            )

        except ExtractError as e:
            summaries.append(
                ChannelSummaryDTO(
                    channel_handle=handle,
                    channel_link=channel_link,
                    summary_text=f"Ошибка получения постов: {e}",
                    post_links=[],
                )
            )
        except SummarizeError as e:
            fallback_links = [p.permalink for p in posts if p.permalink]
            summaries.append(
                ChannelSummaryDTO(
                    channel_handle=handle,
                    channel_link=channel_link,
                    summary_text=f"Ошибка суммаризации: {e}",
                    post_links=fallback_links if include_post_links else [],
                )
            )

    digest = assemble_digest(
        tg_user_id=tg_user_id,
        channel_summaries=summaries,
        created_at=datetime.now(timezone.utc),
        include_post_links=include_post_links,
    )

    chunks = chunk_text_for_telegram(digest.raw_text, max_len=tg_message_max_len)
    if warning:
        chunks = [warning] + chunks

    return AnalyticResponse(digest=digest, chunks=chunks, warning=warning)
