import asyncpg

from src.app.errors import StorageError


async def create_pool(dsn: str) -> asyncpg.Pool:
    try:
        return await asyncpg.create_pool(dsn)
    except Exception as e:
        raise StorageError(str(e)) from e
