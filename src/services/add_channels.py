# FILE: src/services/add_channels.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Orchestrate parser and repository operations for the /add command.
#   SCOPE: Parse raw user input, persist valid channel relations, and return grouped command feedback.
#   DEPENDS: M-PARSING-CHANNELS, M-STORAGE-REPO, M-DOMAIN-TYPES
#   LINKS: docs/development-plan.xml#M-SVC-ADD-CHANNELS, docs/knowledge-graph.xml#M-SVC-ADD-CHANNELS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   AddChannelsResponse — Structured use case response for /add command rendering.
#   add_channels_usecase — Execute parse + persist pipeline and map to AddChannelsResponse.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE contracts and semantic block markers.
# END_CHANGE_SUMMARY

from dataclasses import dataclass

from src.domain.types import ChannelHandle
from src.parsing.channels import parse_channels
from src.storage.repository import add_channels_for_user


@dataclass(frozen=True)
class AddChannelsResponse:
    added: list[ChannelHandle]
    already_present: list[ChannelHandle]
    invalid_tokens: list[str]
    rejected_due_to_limit: list[ChannelHandle]
    truncated_tokens: list[str]


# START_CONTRACT: add_channels_usecase
#   PURPOSE: Process add-channel command payload and persist valid channels for one Telegram user.
#   INPUTS: { pool: asyncpg.Pool, tg_user_id: int, raw_text: str, max_add_per_call: int, max_per_user: int }
#   OUTPUTS: { AddChannelsResponse - grouped outcomes for UI response generation }
#   SIDE_EFFECTS: writes users/channels/user_channels tables through repository layer
#   LINKS: M-SVC-ADD-CHANNELS, M-PARSING-CHANNELS, M-STORAGE-REPO
# END_CONTRACT: add_channels_usecase
async def add_channels_usecase(
    pool,
    tg_user_id: int,
    raw_text: str,
    *,
    max_add_per_call: int,
    max_per_user: int,
) -> AddChannelsResponse:
    # START_BLOCK_PARSE_RAW_CHANNEL_INPUT
    parsed = parse_channels(raw_text, max_items=max_add_per_call)
    # END_BLOCK_PARSE_RAW_CHANNEL_INPUT

    # START_BLOCK_PERSIST_VALID_HANDLES_IF_PRESENT
    if parsed.valid_handles:
        added, already, rejected = await add_channels_for_user(
            pool,
            tg_user_id,
            parsed.valid_handles,
            max_per_user=max_per_user,
        )
    else:
        added, already, rejected = [], [], []
    # END_BLOCK_PERSIST_VALID_HANDLES_IF_PRESENT

    return AddChannelsResponse(
        added=added,
        already_present=already,
        invalid_tokens=parsed.invalid_tokens,
        rejected_due_to_limit=rejected,
        truncated_tokens=parsed.truncated_tokens,
    )
