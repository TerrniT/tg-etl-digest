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


async def add_channels_usecase(
    pool,
    tg_user_id: int,
    raw_text: str,
    *,
    max_add_per_call: int,
    max_per_user: int,
) -> AddChannelsResponse:
    parsed = parse_channels(raw_text, max_items=max_add_per_call)

    if parsed.valid_handles:
        added, already, rejected = await add_channels_for_user(
            pool,
            tg_user_id,
            parsed.valid_handles,
            max_per_user=max_per_user,
        )
    else:
        added, already, rejected = [], [], []

    return AddChannelsResponse(
        added=added,
        already_present=already,
        invalid_tokens=parsed.invalid_tokens,
        rejected_due_to_limit=rejected,
        truncated_tokens=parsed.truncated_tokens,
    )
