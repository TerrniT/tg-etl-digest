from datetime import datetime

from src.domain.dto import ChannelSummaryDTO, DigestDTO

from .formatter import format_channel_block

DELIMITER = "\n\n----------\n\n"


def assemble_digest(
    tg_user_id: int,
    channel_summaries: list[ChannelSummaryDTO],
    *,
    created_at: datetime,
    include_post_links: bool = True,
) -> DigestDTO:
    blocks = [format_channel_block(cs, include_post_links=include_post_links) for cs in channel_summaries]
    raw_text = DELIMITER.join([block for block in blocks if block.strip()])
    return DigestDTO(
        tg_user_id=tg_user_id,
        created_at=created_at,
        channel_summaries=channel_summaries,
        raw_text=raw_text,
    )
