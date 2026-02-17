from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .types import ChannelHandle


@dataclass(frozen=True)
class ParseChannelsResult:
    valid_handles: list[ChannelHandle]
    invalid_tokens: list[str]
    truncated_tokens: list[str]


@dataclass(frozen=True)
class PostDTO:
    channel_handle: ChannelHandle
    tg_msg_id: int
    date: datetime
    text: str
    permalink: Optional[str]


@dataclass(frozen=True)
class ChannelSummaryDTO:
    channel_handle: ChannelHandle
    channel_link: str
    summary_text: str
    post_links: list[str]


@dataclass(frozen=True)
class DigestDTO:
    tg_user_id: int
    created_at: datetime
    channel_summaries: list[ChannelSummaryDTO]
    raw_text: str
