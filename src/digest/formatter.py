from src.domain.dto import ChannelSummaryDTO


def format_channel_block(summary: ChannelSummaryDTO, *, include_post_links: bool = True) -> str:
    lines: list[str] = [summary.channel_link, summary.summary_text.strip()]

    if include_post_links and summary.post_links:
        lines.append("Посты:")
        lines.extend([f"• {link}" for link in summary.post_links])

    return "\n".join(lines).strip()
