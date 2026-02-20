# FILE: src/services/analytic.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Run end-to-end analytic flow for user channels and produce Telegram-ready digest chunks.
#   SCOPE: Load user channels, execute extract-transform-summarize pipeline, handle per-channel failures, chunk output.
#   DEPENDS: M-STORAGE-REPO, M-EXTRACTOR-TELETHON, M-TRANSFORM-POSTS, M-SUMMARIZER-LLM, M-DIGEST-ASSEMBLER, M-DIGEST-CHUNKING, M-DOMAIN-DTO, M-ERRORS
#   LINKS: docs/development-plan.xml#M-SVC-ANALYTIC, docs/knowledge-graph.xml#M-SVC-ANALYTIC
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   AnalyticResponse — Structured result with digest DTO, chunks, and optional warning.
#   analytic_usecase — Execute full /analytic orchestration with per-channel error isolation.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.1.0 - Added per-channel error logging for extract/summarize failures.
# END_CHANGE_SUMMARY

import logging
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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnalyticResponse:
    digest: DigestDTO
    chunks: list[str]
    warning: str | None


# START_CONTRACT: analytic_usecase
#   PURPOSE: Generate digest chunks for all allowed user channels using ETL + summarization flow.
#   INPUTS: { pool: asyncpg.Pool, tg_user_id: int, tg_client: TelegramClient, summarizer: Summarizer, posts_per_channel: int, max_channels_per_call: int, max_chars_per_post: int, tg_message_max_len: int, include_post_links: bool }
#   OUTPUTS: { AnalyticResponse - digest dto, ordered chunk list, optional warning }
#   SIDE_EFFECTS: network I/O to Telegram and OpenAI integrations; reads user-channel data from storage
#   LINKS: M-SVC-ANALYTIC, M-STORAGE-REPO, M-EXTRACTOR-TELETHON, M-SUMMARIZER-LLM, M-DIGEST-ASSEMBLER, M-DIGEST-CHUNKING
# END_CONTRACT: analytic_usecase
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
    # START_BLOCK_LOAD_USER_CHANNELS_AND_LIMIT_GUARDS
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
    # END_BLOCK_LOAD_USER_CHANNELS_AND_LIMIT_GUARDS

    # START_BLOCK_BUILD_CHANNEL_SUMMARIES_WITH_ERROR_ISOLATION
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
            logger.exception(
                "[AnalyticService][analytic_usecase][CHANNEL_EXTRACT_ERROR] handle=%s",
                str(handle),
            )
            summaries.append(
                ChannelSummaryDTO(
                    channel_handle=handle,
                    channel_link=channel_link,
                    summary_text=f"Ошибка получения постов: {e}",
                    post_links=[],
                )
            )
        except SummarizeError as e:
            logger.exception(
                "[AnalyticService][analytic_usecase][CHANNEL_SUMMARIZE_ERROR] handle=%s",
                str(handle),
            )
            fallback_links = [p.permalink for p in posts if p.permalink]
            summaries.append(
                ChannelSummaryDTO(
                    channel_handle=handle,
                    channel_link=channel_link,
                    summary_text=f"Ошибка суммаризации: {e}",
                    post_links=fallback_links if include_post_links else [],
                )
            )
    # END_BLOCK_BUILD_CHANNEL_SUMMARIES_WITH_ERROR_ISOLATION

    # START_BLOCK_ASSEMBLE_AND_CHUNK_FINAL_DIGEST
    digest = assemble_digest(
        tg_user_id=tg_user_id,
        channel_summaries=summaries,
        created_at=datetime.now(timezone.utc),
        include_post_links=include_post_links,
    )

    chunks = chunk_text_for_telegram(digest.raw_text, max_len=tg_message_max_len)
    if warning:
        chunks = [warning] + chunks
    # END_BLOCK_ASSEMBLE_AND_CHUNK_FINAL_DIGEST

    return AnalyticResponse(digest=digest, chunks=chunks, warning=warning)
