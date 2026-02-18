# FILE: src/storage/repository.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Provide repository-level persistence and retrieval operations for users, channels, and posts.
#   SCOPE: Encapsulate asyncpg SQL access with domain error mapping and typed domain outputs.
#   DEPENDS: M-ERRORS, M-DOMAIN-TYPES, M-DOMAIN-DTO
#   LINKS: docs/development-plan.xml#M-STORAGE-REPO, docs/knowledge-graph.xml#M-STORAGE-REPO
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   ensure_user — Ensure user row exists for Telegram user id.
#   list_user_channels — Return user's channel handles ordered by handle.
#   add_channels_for_user — Upsert channels and user relations under per-user limits.
#   remove_channel_for_user — Delete one channel relation for a Telegram user.
#   upsert_posts — Idempotently insert channel posts and report inserted/skipped counts.
#   get_last_posts — Read latest stored posts for a channel and return chronological order.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE contracts and semantic block markers.
# END_CHANGE_SUMMARY

from datetime import datetime

import asyncpg

from src.app.errors import StorageError, ValidationError
from src.domain.dto import PostDTO
from src.domain.types import ChannelHandle


# START_CONTRACT: ensure_user
#   PURPOSE: Ensure user exists in users table and return its internal id.
#   INPUTS: { pool: asyncpg.Pool, tg_user_id: int }
#   OUTPUTS: { int - users.id }
#   SIDE_EFFECTS: insert/update users table
#   LINKS: M-STORAGE-REPO, M-ERRORS
# END_CONTRACT: ensure_user
async def ensure_user(pool: asyncpg.Pool, tg_user_id: int) -> int:
    query = """
        INSERT INTO users(tg_user_id)
        VALUES($1)
        ON CONFLICT (tg_user_id) DO UPDATE SET tg_user_id = EXCLUDED.tg_user_id
        RETURNING id;
    """
    try:
        # START_BLOCK_EXECUTE_USER_UPSERT
        return int(await pool.fetchval(query, tg_user_id))
        # END_BLOCK_EXECUTE_USER_UPSERT
    except Exception as e:
        raise StorageError(str(e)) from e


# START_CONTRACT: list_user_channels
#   PURPOSE: Fetch user's channel list as typed handles.
#   INPUTS: { pool: asyncpg.Pool, tg_user_id: int }
#   OUTPUTS: { list[ChannelHandle] - sorted channel handles }
#   SIDE_EFFECTS: none
#   LINKS: M-STORAGE-REPO, M-DOMAIN-TYPES
# END_CONTRACT: list_user_channels
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
        # START_BLOCK_FETCH_AND_CAST_CHANNEL_HANDLES
        rows = await pool.fetch(query, tg_user_id)
        return [ChannelHandle(row["handle"]) for row in rows]
        # END_BLOCK_FETCH_AND_CAST_CHANNEL_HANDLES
    except Exception as e:
        raise StorageError(str(e)) from e


# START_CONTRACT: add_channels_for_user
#   PURPOSE: Insert user-channel relations for unique handles and classify added/already/rejected sets.
#   INPUTS: { pool: asyncpg.Pool, tg_user_id: int, handles: list[ChannelHandle], max_per_user: int }
#   OUTPUTS: { tuple[list[ChannelHandle], list[ChannelHandle], list[ChannelHandle]] - added/already/rejected }
#   SIDE_EFFECTS: writes users/channels/user_channels tables
#   LINKS: M-STORAGE-REPO, M-DOMAIN-TYPES, M-ERRORS
# END_CONTRACT: add_channels_for_user
async def add_channels_for_user(
    pool: asyncpg.Pool,
    tg_user_id: int,
    handles: list[ChannelHandle],
    *,
    max_per_user: int = 200,
) -> tuple[list[ChannelHandle], list[ChannelHandle], list[ChannelHandle]]:
    # START_BLOCK_VALIDATE_AND_DEDUP_INPUT
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
    # END_BLOCK_VALIDATE_AND_DEDUP_INPUT

    try:
        # START_BLOCK_CALCULATE_ALLOWED_CAPACITY
        user_id = await ensure_user(pool, tg_user_id)
        current_count = int(await pool.fetchval("SELECT COUNT(*) FROM user_channels WHERE user_id = $1", user_id))

        allowed_new = max(0, max_per_user - current_count)
        process_now = unique[:allowed_new]
        rejected = [ChannelHandle(h) for h in unique[allowed_new:]]

        added: list[ChannelHandle] = []
        already: list[ChannelHandle] = []
        # END_BLOCK_CALCULATE_ALLOWED_CAPACITY

        # START_BLOCK_UPSERT_CHANNELS_AND_RELATIONS
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
        # END_BLOCK_UPSERT_CHANNELS_AND_RELATIONS

        return added, already, rejected
    except ValidationError:
        raise
    except Exception as e:
        raise StorageError(str(e)) from e


# START_CONTRACT: remove_channel_for_user
#   PURPOSE: Remove one user-channel relation by tg_user_id and handle.
#   INPUTS: { pool: asyncpg.Pool, tg_user_id: int, handle: ChannelHandle }
#   OUTPUTS: { bool - true when relation removed }
#   SIDE_EFFECTS: deletes from user_channels table
#   LINKS: M-STORAGE-REPO, M-DOMAIN-TYPES
# END_CONTRACT: remove_channel_for_user
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
        # START_BLOCK_DELETE_RELATION_AND_MAP_RESULT
        deleted = await pool.fetchval(query, tg_user_id, str(handle))
        return bool(deleted)
        # END_BLOCK_DELETE_RELATION_AND_MAP_RESULT
    except Exception as e:
        raise StorageError(str(e)) from e


# START_CONTRACT: upsert_posts
#   PURPOSE: Persist posts for one channel with idempotent conflict handling.
#   INPUTS: { pool: asyncpg.Pool, channel_handle: ChannelHandle, posts: list[PostDTO] }
#   OUTPUTS: { tuple[int, int] - inserted_count and skipped_count }
#   SIDE_EFFECTS: writes channels/posts tables
#   LINKS: M-STORAGE-REPO, M-DOMAIN-DTO, M-DOMAIN-TYPES
# END_CONTRACT: upsert_posts
async def upsert_posts(
    pool: asyncpg.Pool,
    channel_handle: ChannelHandle,
    posts: list[PostDTO],
) -> tuple[int, int]:
    # START_BLOCK_HANDLE_EMPTY_POST_BATCH
    if not posts:
        return 0, 0
    # END_BLOCK_HANDLE_EMPTY_POST_BATCH

    inserted_count = 0
    try:
        # START_BLOCK_UPSERT_CHANNEL_AND_POST_ROWS
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
        # END_BLOCK_UPSERT_CHANNEL_AND_POST_ROWS

        skipped = len(posts) - inserted_count
        return inserted_count, skipped
    except Exception as e:
        raise StorageError(str(e)) from e


# START_CONTRACT: get_last_posts
#   PURPOSE: Read latest stored posts for channel and return chronological order.
#   INPUTS: { pool: asyncpg.Pool, channel_handle: ChannelHandle, limit: int }
#   OUTPUTS: { list[PostDTO] - chronologically ordered post list }
#   SIDE_EFFECTS: none
#   LINKS: M-STORAGE-REPO, M-DOMAIN-DTO, M-DOMAIN-TYPES
# END_CONTRACT: get_last_posts
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
        # START_BLOCK_FETCH_ROWS_AND_CAST_TO_DTO
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
        # END_BLOCK_FETCH_ROWS_AND_CAST_TO_DTO

        # START_BLOCK_RESTORE_CHRONOLOGICAL_ORDER
        return list(reversed(out))
        # END_BLOCK_RESTORE_CHRONOLOGICAL_ORDER
    except Exception as e:
        raise StorageError(str(e)) from e
