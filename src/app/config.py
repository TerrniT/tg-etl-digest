# FILE: src/app/config.py
# VERSION: 1.0.1
# START_MODULE_CONTRACT
#   PURPOSE: Load and validate runtime configuration from environment variables.
#   SCOPE: Build typed Config object with required credentials and operational limits.
#   DEPENDS: none
#   LINKS: docs/development-plan.xml#M-CONFIG, docs/knowledge-graph.xml#M-CONFIG
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   Config — Runtime configuration dataclass.
#   load_config — Read env vars and return Config with defaults for optional limits.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.1 - Added missing `openai_base_url` Config field to match runtime loader usage.
# END_CHANGE_SUMMARY

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
    openai_base_url: str
    openai_model: str
    max_add_per_call: int
    max_channels_per_user: int
    max_channels_per_analytic_call: int
    posts_per_channel: int
    max_chars_per_post: int
    tg_message_max_len: int
    include_post_links: bool


# START_CONTRACT: load_config
#   PURPOSE: Resolve required and optional configuration values from environment.
#   INPUTS: {}
#   OUTPUTS: { Config - validated runtime config }
#   SIDE_EFFECTS: reads process environment and .env file
#   LINKS: M-CONFIG
# END_CONTRACT: load_config
def load_config() -> Config:
    # START_BLOCK_LOAD_ENV_SOURCES
    load_dotenv()
    # END_BLOCK_LOAD_ENV_SOURCES

    # START_BLOCK_DEFINE_REQUIRED_VALUE_HELPER
    def must(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"Missing env var: {name}")
        return value
    # END_BLOCK_DEFINE_REQUIRED_VALUE_HELPER

    # START_BLOCK_BUILD_TYPED_CONFIG
    return Config(
        bot_token=must("BOT_TOKEN"),
        database_url=must("DATABASE_URL"),
        tg_api_id=int(must("TG_API_ID")),
        tg_api_hash=must("TG_API_HASH"),
        telethon_session_name=must("TELETHON_SESSION_NAME"),
        openai_api_key=must("AI_API_KEY"),
        openai_base_url=must("AI_BASE_URL"),
        openai_model=os.getenv("AI_MODEL", "qwen-coder"),
        max_add_per_call=int(os.getenv("MAX_ADD_PER_CALL", "50")),
        max_channels_per_user=int(os.getenv("MAX_CHANNELS_PER_USER", "200")),
        max_channels_per_analytic_call=int(os.getenv("MAX_CHANNELS_PER_ANALYTIC_CALL", "50")),
        posts_per_channel=int(os.getenv("POSTS_PER_CHANNEL", "5")),
        max_chars_per_post=int(os.getenv("MAX_CHARS_PER_POST", "1500")),
        tg_message_max_len=int(os.getenv("TG_MESSAGE_MAX_LEN", "3500")),
        include_post_links=os.getenv("INCLUDE_POST_LINKS", "true").lower() == "true",
    )
    # END_BLOCK_BUILD_TYPED_CONFIG
