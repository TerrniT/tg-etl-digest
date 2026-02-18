from datetime import datetime

import asyncpg

from src.app.errors import StorageError, ValidationError
from src.domain.dto import PostDTO
from src.domain.types import ChannelHandle


async def ensure_user(pool: asyncpg.Pool, tg_user_id: int) -> int:
    query = """
        INSERT INTO users(tg_user_id)
        VALUES($1)
        ON CONFLICT (tg_user_id) DO UPDATE SET tg_user_id = EXCLUDED.tg_user_id
        RETURNING id;
    """
    try:
        return int(await pool.fetchval(query, tg_user_id))
    except Exception as e:
        raise StorageError(str(e)) from e


async def list_user_channels(pool: asyncpg.Pool, tg_user_id: int) -> list[ChannelHandle]:
    query = """
        SELECT c.handle
        FROM users u
        JOIN user_channels uc ON uc.user_id = u.id
        JOIN channels c ON c.id = uc.channel_id
        WHERE u.tg_user_id = $1
        ORDER BY c.handle ASC;
    """
    try:
        rows = await pool.fetch(query, tg_user_id)
        return [ChannelHandle(row["handle"]) for row in rows]
    except Exception as e:
        raise StorageError(str(e)) from e


async def add_channels_for_user(
    pool: asyncpg.Pool,
    tg_user_id: int,
    handles: list[ChannelHandle],
    *,
    max_per_user: int = 200,
) -> tuple[list[ChannelHandle], list[ChannelHandle], list[ChannelHandle]]:
    if not handles:
        raise ValidationError("handles is empty")

    unique: list[str] = []
    seen = set()
    for h in handles:
        v = str(h)
        if v in seen:
            continue
        seen.add(v)
        unique.append(v)

    try:
        user_id = await ensure_user(pool, tg_user_id)
        current_count = int(await pool.fetchval("SELECT COUNT(*) FROM user_channels WHERE user_id = $1", user_id))

        allowed_new = max(0, max_per_user - current_count)
        process_now = unique[:allowed_new]
        rejected = [ChannelHandle(h) for h in unique[allowed_new:]]

        added: list[ChannelHandle] = []
        already: list[ChannelHandle] = []

        async with pool.acquire() as conn:
            async with conn.transaction():
                for handle in process_now:
                    channel_id = await conn.fetchval(
                        """
                        INSERT INTO channels(handle)
                        VALUES($1)
                        ON CONFLICT (handle) DO UPDATE SET handle = EXCLUDED.handle
                        RETURNING id;
                        """,
                        handle,
                    )

                    inserted = await conn.fetchval(
                        """
                        INSERT INTO user_channels(user_id, channel_id)
                        VALUES($1, $2)
                        ON CONFLICT (user_id, channel_id) DO NOTHING
                        RETURNING 1;
                        """,
                        user_id,
                        channel_id,
                    )
                    if inserted:
                        added.append(ChannelHandle(handle))
                    else:
                        already.append(ChannelHandle(handle))

        return added, already, rejected
    except ValidationError:
        raise
    except Exception as e:
        raise StorageError(str(e)) from e


async def remove_channel_for_user(pool: asyncpg.Pool, tg_user_id: int, handle: ChannelHandle) -> bool:
    query = """
        DELETE FROM user_channels uc
        USING users u, channels c
        WHERE uc.user_id = u.id
          AND uc.channel_id = c.id
          AND u.tg_user_id = $1
          AND c.handle = $2
        RETURNING 1;
    """
    try:
        deleted = await pool.fetchval(query, tg_user_id, str(handle))
        return bool(deleted)
    except Exception as e:
        raise StorageError(str(e)) from e


async def upsert_posts(
    pool: asyncpg.Pool,
    channel_handle: ChannelHandle,
    posts: list[PostDTO],
) -> tuple[int, int]:
    if not posts:
        return 0, 0

    inserted_count = 0
    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                channel_id = await conn.fetchval(
                    """
                    INSERT INTO channels(handle)
                    VALUES($1)
                    ON CONFLICT (handle) DO UPDATE SET handle = EXCLUDED.handle
                    RETURNING id;
                    """,
                    str(channel_handle),
                )

                for post in posts:
                    inserted = await conn.fetchval(
                        """
                        INSERT INTO posts(channel_id, tg_msg_id, date, text, permalink)
                        VALUES($1, $2, $3, $4, $5)
                        ON CONFLICT (channel_id, tg_msg_id) DO NOTHING
                        RETURNING 1;
                        """,
                        channel_id,
                        post.tg_msg_id,
                        post.date,
                        post.text,
                        post.permalink,
                    )
                    if inserted:
                        inserted_count += 1

        skipped = len(posts) - inserted_count
        return inserted_count, skipped
    except Exception as e:
        raise StorageError(str(e)) from e


async def get_last_posts(pool: asyncpg.Pool, channel_handle: ChannelHandle, limit: int) -> list[PostDTO]:
    query = """
        SELECT c.handle, p.tg_msg_id, p.date, p.text, p.permalink
        FROM channels c
        JOIN posts p ON p.channel_id = c.id
        WHERE c.handle = $1
        ORDER BY p.date DESC
        LIMIT $2;
    """
    try:
        rows = await pool.fetch(query, str(channel_handle), limit)
        out = [
            PostDTO(
                channel_handle=ChannelHandle(row["handle"]),
                tg_msg_id=int(row["tg_msg_id"]),
                date=row["date"] if isinstance(row["date"], datetime) else datetime.fromisoformat(str(row["date"])),
                text=row["text"] or "",
                permalink=row["permalink"],
            )
            for row in rows
        ]
        return list(reversed(out))
    except Exception as e:
        raise StorageError(str(e)) from e
