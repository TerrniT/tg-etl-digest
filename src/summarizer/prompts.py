# FILE: src/summarizer/prompts.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Build deterministic Russian prompt template for channel summarization.
#   SCOPE: Serialize channel context and transformed posts into one LLM input string.
#   DEPENDS: M-DOMAIN-TYPES, M-DOMAIN-DTO
#   LINKS: docs/development-plan.xml#M-SUMMARIZER-PROMPTS, docs/knowledge-graph.xml#M-SUMMARIZER-PROMPTS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   build_summary_prompt — Construct LLM prompt for one channel from normalized post list.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE contracts and semantic block markers.
# END_CHANGE_SUMMARY

from src.domain.dto import PostDTO
from src.domain.types import ChannelHandle


# START_CONTRACT: build_summary_prompt
#   PURPOSE: Generate one stable summarization prompt containing channel metadata and recent posts.
#   INPUTS: { channel_handle: ChannelHandle, channel_link: str, posts: list[PostDTO] }
#   OUTPUTS: { str - prompt text for LLM request }
#   SIDE_EFFECTS: none
#   LINKS: M-SUMMARIZER-PROMPTS, M-DOMAIN-TYPES, M-DOMAIN-DTO
# END_CONTRACT: build_summary_prompt
def build_summary_prompt(
    channel_handle: ChannelHandle,
    channel_link: str,
    posts: list[PostDTO],
) -> str:
    # START_BLOCK_SERIALIZE_POSTS_FOR_PROMPT
    joined = "\n\n".join(
        [f"POST #{i + 1} ({p.permalink or 'no-link'}):\n{p.text}" for i, p in enumerate(posts)]
    )
    # END_BLOCK_SERIALIZE_POSTS_FOR_PROMPT

    # START_BLOCK_BUILD_PROMPT_TEMPLATE
    return (
        "Ты делаешь дайджест телеграм-канала.\n"
        f"Канал: {str(channel_handle)}\n"
        f"Ссылка: {channel_link}\n\n"
        "Суммаризируй последние посты.\n"
        "Требования:\n"
        "- 4-8 буллетов, коротко и по делу\n"
        "- Без воды, без повторов\n"
        "- Если есть цифры/факты/анонсы/сроки — обязательно упомяни\n"
        "- Язык: русский\n\n"
        f"Посты:\n{joined}\n"
    )
    # END_BLOCK_BUILD_PROMPT_TEMPLATE
