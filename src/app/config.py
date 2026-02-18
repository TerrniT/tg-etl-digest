import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    bot_token: str
    database_url: str
    tg_api_id: int
    tg_api_hash: str
    telethon_session_name: str
    openai_api_key: str
    openai_model: str
    max_add_per_call: int
    max_channels_per_user: int
    max_channels_per_analytic_call: int
    posts_per_channel: int
    max_chars_per_post: int
    tg_message_max_len: int
    include_post_links: bool


def load_config() -> Config:
    load_dotenv()

    def must(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"Missing env var: {name}")
        return value

    return Config(
        bot_token=must("BOT_TOKEN"),
        database_url=must("DATABASE_URL"),
        tg_api_id=int(must("TG_API_ID")),
        tg_api_hash=must("TG_API_HASH"),
        telethon_session_name=must("TELETHON_SESSION_NAME"),
        openai_api_key=must("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        max_add_per_call=int(os.getenv("MAX_ADD_PER_CALL", "50")),
        max_channels_per_user=int(os.getenv("MAX_CHANNELS_PER_USER", "200")),
        max_channels_per_analytic_call=int(os.getenv("MAX_CHANNELS_PER_ANALYTIC_CALL", "50")),
        posts_per_channel=int(os.getenv("POSTS_PER_CHANNEL", "5")),
        max_chars_per_post=int(os.getenv("MAX_CHARS_PER_POST", "1500")),
        tg_message_max_len=int(os.getenv("TG_MESSAGE_MAX_LEN", "3500")),
        include_post_links=os.getenv("INCLUDE_POST_LINKS", "true").lower() == "true",
    )
