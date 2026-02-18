# FILE: src/digest/formatter.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Convert channel summary DTO into one printable digest block.
#   SCOPE: Render channel link, summary body, and optional post links in stable order.
#   DEPENDS: M-DOMAIN-DTO
#   LINKS: docs/development-plan.xml#M-DIGEST-FORMATTER, docs/knowledge-graph.xml#M-DIGEST-FORMATTER
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   format_channel_block — Render one ChannelSummaryDTO to text block for digest assembly.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE contracts and semantic block markers.
# END_CHANGE_SUMMARY

from src.domain.dto import ChannelSummaryDTO


# START_CONTRACT: format_channel_block
#   PURPOSE: Render one channel summary into final textual block used by digest assembler.
#   INPUTS: { summary: ChannelSummaryDTO, include_post_links: bool }
#   OUTPUTS: { str - formatted channel block }
#   SIDE_EFFECTS: none
#   LINKS: M-DIGEST-FORMATTER, M-DOMAIN-DTO
# END_CONTRACT: format_channel_block
def format_channel_block(summary: ChannelSummaryDTO, *, include_post_links: bool = True) -> str:
    # START_BLOCK_RENDER_BASE_LINES
    lines: list[str] = [summary.channel_link, summary.summary_text.strip()]
    # END_BLOCK_RENDER_BASE_LINES

    # START_BLOCK_OPTIONAL_POST_LINKS_SECTION
    if include_post_links and summary.post_links:
        lines.append("Посты:")
        lines.extend([f"• {link}" for link in summary.post_links])
    # END_BLOCK_OPTIONAL_POST_LINKS_SECTION

    return "\n".join(lines).strip()
