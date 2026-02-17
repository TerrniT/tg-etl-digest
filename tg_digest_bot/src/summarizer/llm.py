import asyncio

from openai import OpenAI

from src.app.errors import SummarizeError, ValidationError
from src.domain.dto import PostDTO
from src.domain.types import ChannelHandle

from .prompts import build_summary_prompt


class Summarizer:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    async def summarize_channel(
        self,
        channel_handle: ChannelHandle,
        channel_link: str,
        posts: list[PostDTO],
    ) -> str:
        if not posts:
            raise ValidationError("posts is empty")

        prompt = build_summary_prompt(channel_handle, channel_link, posts)

        try:
            resp = await asyncio.to_thread(
                self._client.responses.create,
                model=self._model,
                input=prompt,
            )
            text = (resp.output_text or "").strip()
            if not text:
                raise SummarizeError("empty summary from LLM")
            return text
        except Exception as e:
            raise SummarizeError(str(e)) from e
