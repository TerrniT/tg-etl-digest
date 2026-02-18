# FILE: src/extractor/telethon_extractor.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Fetch recent text posts from Telegram channels through Telethon MTProto client.
#   SCOPE: Resolve channel entity, iterate messages, normalize text/date/permalink, and map integration errors.
#   DEPENDS: M-ERRORS, M-DOMAIN-TYPES, M-DOMAIN-DTO, M-TRANSFORM-TEXT
#   LINKS: docs/development-plan.xml#M-EXTRACTOR-TELETHON, docs/knowledge-graph.xml#M-EXTRACTOR-TELETHON
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   fetch_last_posts — Collect recent text posts and convert them to PostDTO list.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE contracts and semantic block markers.
# END_CHANGE_SUMMARY

from datetime import timezone

from telethon import TelegramClient
from telethon.errors import FloodWaitError

from src.app.errors import ExtractError
from src.domain.dto import PostDTO
from src.domain.types import ChannelHandle
from src.transform.text import clean_text


# START_CONTRACT: fetch_last_posts
#   PURPOSE: Fetch last text messages for one channel and normalize them into PostDTO objects.
#   INPUTS: { client: TelegramClient, channel_handle: ChannelHandle, limit: int }
#   OUTPUTS: { list[PostDTO] - chronologically ordered list of text posts up to limit }
#   SIDE_EFFECTS: network I/O to Telegram MTProto API
#   LINKS: M-EXTRACTOR-TELETHON, M-TRANSFORM-TEXT, M-DOMAIN-DTO
# END_CONTRACT: fetch_last_posts
async def fetch_last_posts(
    client: TelegramClient,
    channel_handle: ChannelHandle,
    *,
    limit: int = 5,
) -> list[PostDTO]:
    try:
        # START_BLOCK_RESOLVE_ENTITY_AND_INIT_COLLECTION
        entity = await client.get_entity(str(channel_handle))

        collected: list[PostDTO] = []
        scan_limit = max(limit * 4, limit)
        # END_BLOCK_RESOLVE_ENTITY_AND_INIT_COLLECTION

        # START_BLOCK_ITERATE_MESSAGES_AND_BUILD_DTOS
        async for msg in client.iter_messages(entity, limit=scan_limit):
            if len(collected) >= limit:
                break
            text = clean_text(getattr(msg, "message", "") or "")
            if not text:
                continue
            msg_id = int(msg.id)
            permalink = f"https://t.me/{str(channel_handle)}/{msg_id}" if getattr(entity, "username", None) else None
            dt = msg.date
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            collected.append(
                PostDTO(
                    channel_handle=channel_handle,
                    tg_msg_id=msg_id,
                    date=dt,
                    text=text,
                    permalink=permalink,
                )
            )
        # END_BLOCK_ITERATE_MESSAGES_AND_BUILD_DTOS

        # START_BLOCK_FINALIZE_ORDER_AND_RETURN
        collected.reverse()
        return collected
        # END_BLOCK_FINALIZE_ORDER_AND_RETURN
    except FloodWaitError as e:
        raise ExtractError(f"FloodWait {e.seconds}s") from e
    except Exception as e:
        raise ExtractError(str(e)) from e
