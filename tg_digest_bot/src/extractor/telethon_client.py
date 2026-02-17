from telethon import TelegramClient

from src.app.errors import ExtractError


async def create_telethon_client(session_name: str, api_id: int, api_hash: str) -> TelegramClient:
    try:
        client = TelegramClient(session_name, api_id, api_hash)
        await client.start()
        return client
    except Exception as e:
        raise ExtractError(str(e)) from e
