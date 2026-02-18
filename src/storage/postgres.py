# FILE: src/storage/postgres.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Initialize PostgreSQL connection pool for repository layer.
#   SCOPE: Wrap asyncpg pool creation with domain-specific error mapping.
#   DEPENDS: M-ERRORS
#   LINKS: docs/development-plan.xml#M-STORAGE-POOL, docs/knowledge-graph.xml#M-STORAGE-POOL
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   create_pool — Build asyncpg pool and map low-level failures to StorageError.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE contracts and semantic block markers.
# END_CHANGE_SUMMARY

import asyncpg

from src.app.errors import StorageError


# START_CONTRACT: create_pool
#   PURPOSE: Create asyncpg pool from DSN and surface storage-level errors.
#   INPUTS: { dsn: str }
#   OUTPUTS: { asyncpg.Pool }
#   SIDE_EFFECTS: opens DB connections
#   LINKS: M-STORAGE-POOL, M-ERRORS
# END_CONTRACT: create_pool
async def create_pool(dsn: str) -> asyncpg.Pool:
    try:
        # START_BLOCK_CREATE_ASYNCPG_POOL
        return await asyncpg.create_pool(dsn)
        # END_BLOCK_CREATE_ASYNCPG_POOL
    except Exception as e:
        raise StorageError(str(e)) from e
