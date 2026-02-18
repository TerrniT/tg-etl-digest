# FILE: src/domain/dto.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Define immutable DTOs shared across parser, ETL pipeline, and digest delivery.
#   SCOPE: Provide structured data contracts for parse results, posts, channel summaries, and digests.
#   DEPENDS: M-DOMAIN-TYPES
#   LINKS: docs/development-plan.xml#M-DOMAIN-DTO, docs/knowledge-graph.xml#M-DOMAIN-DTO
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   ParseChannelsResult — Result grouping for parsed channel input.
#   PostDTO — Normalized channel post payload.
#   ChannelSummaryDTO — Per-channel digest block payload.
#   DigestDTO — Full digest payload for chunking and delivery.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE module contract and map.
# END_CHANGE_SUMMARY

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
