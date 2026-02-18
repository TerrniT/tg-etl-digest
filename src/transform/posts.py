from src.domain.dto import PostDTO

from .text import clean_text, truncate_text


def transform_posts(
    posts: list[PostDTO],
    *,
    max_chars_per_post: int = 1500,
    min_chars_per_post: int = 1,
) -> list[PostDTO]:
    out: list[PostDTO] = []
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
    return out
