# FILE: src/summarizer/llm.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Provide OpenAI-backed channel summarization adapter.
#   SCOPE: Build prompts, call Responses API, validate text output, and map exceptions to domain errors.
#   DEPENDS: M-ERRORS, M-SUMMARIZER-PROMPTS, M-DOMAIN-TYPES, M-DOMAIN-DTO
#   LINKS: docs/development-plan.xml#M-SUMMARIZER-LLM, docs/knowledge-graph.xml#M-SUMMARIZER-LLM
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   Summarizer — OpenAI adapter class for channel summary generation.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE contracts and semantic block markers.
# END_CHANGE_SUMMARY

import asyncio

from openai import OpenAI

from src.app.errors import SummarizeError, ValidationError
from src.domain.dto import PostDTO
from src.domain.types import ChannelHandle

from .prompts import build_summary_prompt


class Summarizer:
    # START_CONTRACT: Summarizer.__init__
    #   PURPOSE: Initialize OpenAI client wrapper with configured API key and model.
    #   INPUTS: { api_key: str, model: str, base_url: str }
    #   OUTPUTS: { None }
    #   SIDE_EFFECTS: creates OpenAI client instance
    #   LINKS: M-SUMMARIZER-LLM
    # END_CONTRACT: Summarizer.__init__
    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        # START_BLOCK_INIT_OPENAI_CLIENT
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        # END_BLOCK_INIT_OPENAI_CLIENT

    # START_CONTRACT: Summarizer.summarize_channel
    #   PURPOSE: Summarize transformed channel posts into concise Russian digest text.
    #   INPUTS: { channel_handle: ChannelHandle, channel_link: str, posts: list[PostDTO] }
    #   OUTPUTS: { str - non-empty summary text }
    #   SIDE_EFFECTS: network I/O to OpenAI Responses API
    #   LINKS: M-SUMMARIZER-LLM, M-SUMMARIZER-PROMPTS
    # END_CONTRACT: Summarizer.summarize_channel
    async def summarize_channel(
        self,
        channel_handle: ChannelHandle,
        channel_link: str,
        posts: list[PostDTO],
    ) -> str:
        # START_BLOCK_VALIDATE_INPUT_AND_BUILD_PROMPT
        if not posts:
            raise ValidationError("posts is empty")

        prompt = build_summary_prompt(channel_handle, channel_link, posts)
        # END_BLOCK_VALIDATE_INPUT_AND_BUILD_PROMPT

        try:
            # START_BLOCK_CALL_OPENAI_AND_VALIDATE_RESPONSE
            resp = await asyncio.to_thread(
                self._client.responses.create,
                model=self._model,
                input=prompt,
            )
            text = (resp.output_text or "").strip()
            if not text:
                raise SummarizeError("empty summary from LLM")
            return text
            # END_BLOCK_CALL_OPENAI_AND_VALIDATE_RESPONSE
        except Exception as e:
            raise SummarizeError(str(e)) from e
