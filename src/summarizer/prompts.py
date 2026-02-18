from src.domain.dto import PostDTO
from src.domain.types import ChannelHandle


def build_summary_prompt(
    channel_handle: ChannelHandle,
    channel_link: str,
    posts: list[PostDTO],
) -> str:
    joined = "\n\n".join(
        [f"POST #{i + 1} ({p.permalink or 'no-link'}):\n{p.text}" for i, p in enumerate(posts)]
    )
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
