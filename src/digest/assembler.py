# FILE: src/digest/assembler.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Assemble channel summaries into a final digest DTO with stable block delimiter.
#   SCOPE: Render per-channel blocks and compose DigestDTO payload for downstream chunking.
#   DEPENDS: M-DOMAIN-DTO, M-DIGEST-FORMATTER
#   LINKS: docs/development-plan.xml#M-DIGEST-ASSEMBLER, docs/knowledge-graph.xml#M-DIGEST-ASSEMBLER
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   DELIMITER — Canonical separator used between digest channel blocks.
#   assemble_digest — Build DigestDTO from channel summaries and rendered block text.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE contracts and semantic block markers.
# END_CHANGE_SUMMARY

from datetime import datetime

from src.domain.dto import ChannelSummaryDTO, DigestDTO

from .formatter import format_channel_block

DELIMITER = "\n\n----------\n\n"


# START_CONTRACT: assemble_digest
#   PURPOSE: Build digest DTO from channel summaries and formatted block text.
#   INPUTS: { tg_user_id: int, channel_summaries: list[ChannelSummaryDTO], created_at: datetime, include_post_links: bool }
#   OUTPUTS: { DigestDTO - digest payload containing rendered text and source summaries }
#   SIDE_EFFECTS: none
#   LINKS: M-DIGEST-ASSEMBLER, M-DIGEST-FORMATTER, M-DOMAIN-DTO
# END_CONTRACT: assemble_digest
def assemble_digest(
    tg_user_id: int,
    channel_summaries: list[ChannelSummaryDTO],
    *,
    created_at: datetime,
    include_post_links: bool = True,
) -> DigestDTO:
    # START_BLOCK_RENDER_CHANNEL_BLOCKS
    blocks = [format_channel_block(cs, include_post_links=include_post_links) for cs in channel_summaries]
    # END_BLOCK_RENDER_CHANNEL_BLOCKS

    # START_BLOCK_BUILD_DIGEST_TEXT
    raw_text = DELIMITER.join([block for block in blocks if block.strip()])
    # END_BLOCK_BUILD_DIGEST_TEXT

    return DigestDTO(
        tg_user_id=tg_user_id,
        created_at=created_at,
        channel_summaries=channel_summaries,
        raw_text=raw_text,
    )
