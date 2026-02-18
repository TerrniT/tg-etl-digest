# FILE: src/transform/posts.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Normalize extracted posts for summarization by cleaning and truncating text payloads.
#   SCOPE: Apply text hygiene and minimum-length filtering while preserving post metadata.
#   DEPENDS: M-DOMAIN-DTO, M-TRANSFORM-TEXT
#   LINKS: docs/development-plan.xml#M-TRANSFORM-POSTS, docs/knowledge-graph.xml#M-TRANSFORM-POSTS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   transform_posts — Clean/truncate post text and drop posts below minimal text length.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE contracts and semantic block markers.
# END_CHANGE_SUMMARY

from src.domain.dto import PostDTO

from .text import clean_text, truncate_text


# START_CONTRACT: transform_posts
#   PURPOSE: Prepare extracted posts for summarizer input by cleaning and truncating text content.
#   INPUTS: { posts: list[PostDTO], max_chars_per_post: int, min_chars_per_post: int }
#   OUTPUTS: { list[PostDTO] - transformed post list preserving source metadata }
#   SIDE_EFFECTS: none
#   LINKS: M-TRANSFORM-POSTS, M-TRANSFORM-TEXT
# END_CONTRACT: transform_posts
def transform_posts(
    posts: list[PostDTO],
    *,
    max_chars_per_post: int = 1500,
    min_chars_per_post: int = 1,
) -> list[PostDTO]:
    # START_BLOCK_INIT_TRANSFORM_OUTPUT
    out: list[PostDTO] = []
    # END_BLOCK_INIT_TRANSFORM_OUTPUT

    # START_BLOCK_TRANSFORM_AND_FILTER_POSTS
    for p in posts:
        text = truncate_text(clean_text(p.text), max_chars_per_post)
        if len(text) < min_chars_per_post:
            continue
        out.append(
            PostDTO(
                channel_handle=p.channel_handle,
                tg_msg_id=p.tg_msg_id,
                date=p.date,
                text=text,
                permalink=p.permalink,
            )
        )
    # END_BLOCK_TRANSFORM_AND_FILTER_POSTS

    return out
