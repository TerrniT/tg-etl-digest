from datetime import timezone

from telethon import TelegramClient
from telethon.errors import FloodWaitError

from src.app.errors import ExtractError
from src.domain.dto import PostDTO
from src.domain.types import ChannelHandle
from src.transform.text import clean_text


async def fetch_last_posts(
    client: TelegramClient,
    channel_handle: ChannelHandle,
    *,
    limit: int = 5,
) -> list[PostDTO]:
    try:
        entity = await client.get_entity(str(channel_handle))

        collected: list[PostDTO] = []
        scan_limit = max(limit * 4, limit)
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

        collected.reverse()
        return collected
    except FloodWaitError as e:
        raise ExtractError(f"FloodWait {e.seconds}s") from e
    except Exception as e:
        raise ExtractError(str(e)) from e
