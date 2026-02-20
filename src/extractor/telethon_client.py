# FILE: src/extractor/telethon_client.py
# VERSION: 1.1.0
# START_MODULE_CONTRACT
#   PURPOSE: Build and start Telethon client session for channel extraction.
#   SCOPE: Initialize TelegramClient with credentials and map startup failures.
#   DEPENDS: M-ERRORS
#   LINKS: docs/development-plan.xml#M-TELETHON-CLIENT, docs/knowledge-graph.xml#M-TELETHON-CLIENT
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   create_telethon_client — Create and start Telethon client instance.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.1.0 - Added startup validation to reject bot-authorized Telethon sessions for channel history extraction.
# END_CHANGE_SUMMARY

from telethon import TelegramClient

from src.app.errors import ExtractError


# START_CONTRACT: create_telethon_client
#   PURPOSE: Initialize and start Telethon client for MTProto requests.
#   INPUTS: { session_name: str, api_id: int, api_hash: str }
#   OUTPUTS: { TelegramClient }
#   SIDE_EFFECTS: starts Telethon session and network connection
#   LINKS: M-TELETHON-CLIENT, M-ERRORS
# END_CONTRACT: create_telethon_client
async def create_telethon_client(session_name: str, api_id: int, api_hash: str) -> TelegramClient:
    try:
        # START_BLOCK_INIT_START_AND_VALIDATE_USER_SESSION
        client = TelegramClient(session_name, api_id, api_hash)
        await client.start()
        me = await client.get_me()
        if getattr(me, "bot", False):
            raise ExtractError(
                "Telethon session is authorized as bot account. "
                "Channel history extraction requires a user MTProto session (phone login)."
            )
        return client
        # END_BLOCK_INIT_START_AND_VALIDATE_USER_SESSION
    except Exception as e:
        raise ExtractError(str(e)) from e
