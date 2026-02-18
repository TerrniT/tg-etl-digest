# FILE: src/parsing/channels.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Normalize and validate channel tokens into deduplicated ChannelHandle values.
#   SCOPE: Handle parsing for /add and /remove flows including invalid/truncated token tracking.
#   DEPENDS: M-DOMAIN-TYPES, M-DOMAIN-DTO
#   LINKS: docs/development-plan.xml#M-PARSING-CHANNELS, docs/knowledge-graph.xml#M-PARSING-CHANNELS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   normalize_handle — Normalize one raw token into ChannelHandle or None.
#   parse_channels — Parse full input text into valid, invalid, and truncated token groups.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE contracts and semantic block markers for parser flow.
# END_CHANGE_SUMMARY

import re
from typing import Optional

from src.domain.dto import ParseChannelsResult
from src.domain.types import ChannelHandle

USERNAME_RE = re.compile(r"^[a-z0-9_]{5,32}$")
TRAILING_PUNCT_RE = re.compile(r"[)\]\}\.,;:!?]+$")
SPLIT_RE = re.compile(r"[\s,]+")


def _is_valid_username(handle: str) -> bool:
    if not USERNAME_RE.fullmatch(handle):
        return False
    if handle.startswith("_") or handle.endswith("_"):
        return False
    if "__" in handle:
        return False
    return True


# START_CONTRACT: normalize_handle
#   PURPOSE: Convert a raw token into canonical ChannelHandle if token matches Telegram username rules.
#   INPUTS: { raw: str - token in @handle, handle, or t.me URL form }
#   OUTPUTS: { Optional[ChannelHandle] - normalized handle or None for invalid token }
#   SIDE_EFFECTS: none
#   LINKS: M-PARSING-CHANNELS, M-DOMAIN-TYPES
# END_CONTRACT: normalize_handle
def normalize_handle(raw: str) -> Optional[ChannelHandle]:
    # START_BLOCK_NORMALIZE_PRIMITIVE_TOKEN
    token = (raw or "").strip()
    if not token:
        return None

    token = TRAILING_PUNCT_RE.sub("", token)
    token = token.strip()
    if not token:
        return None
    # END_BLOCK_NORMALIZE_PRIMITIVE_TOKEN

    # START_BLOCK_STRIP_URL_PREFIXES
    token = re.sub(r"^https?://", "", token, flags=re.IGNORECASE)

    if token.lower().startswith("t.me/"):
        token = token[5:]
    elif token.lower().startswith("telegram.me/"):
        token = token[12:]
    # END_BLOCK_STRIP_URL_PREFIXES

    # START_BLOCK_VALIDATE_TELEGRAM_USERNAME_RULES
    token = token.lstrip("@").strip()
    if not token:
        return None

    low = token.lower()
    if low.startswith("+") or low.startswith("joinchat"):
        return None
    if "/" in token:
        return None
    if not _is_valid_username(low):
        return None
    # END_BLOCK_VALIDATE_TELEGRAM_USERNAME_RULES

    return ChannelHandle(low)


# START_CONTRACT: parse_channels
#   PURPOSE: Parse user input text into deduplicated valid handles and explicit invalid/truncated groups.
#   INPUTS: { text: str - raw command payload, max_items: int - max valid handles to accept }
#   OUTPUTS: { ParseChannelsResult - grouped parser output with stable ordering }
#   SIDE_EFFECTS: none
#   LINKS: M-PARSING-CHANNELS, M-DOMAIN-DTO
# END_CONTRACT: parse_channels
def parse_channels(text: str, *, max_items: int = 50) -> ParseChannelsResult:
    # START_BLOCK_SPLIT_AND_INIT_ACCUMULATORS
    tokens = [t for t in SPLIT_RE.split((text or "").strip()) if t]

    valid: list[ChannelHandle] = []
    invalid: list[str] = []
    truncated: list[str] = []
    seen: set[str] = set()
    # END_BLOCK_SPLIT_AND_INIT_ACCUMULATORS

    # START_BLOCK_CLASSIFY_TOKENS_AND_APPLY_LIMITS
    for raw_token in tokens:
        normalized = normalize_handle(raw_token)
        if normalized is None:
            invalid.append(raw_token.strip())
            continue

        key = str(normalized)
        if key in seen:
            continue

        seen.add(key)
        if len(valid) < max_items:
            valid.append(normalized)
        else:
            truncated.append(raw_token.strip())
    # END_BLOCK_CLASSIFY_TOKENS_AND_APPLY_LIMITS

    return ParseChannelsResult(valid_handles=valid, invalid_tokens=invalid, truncated_tokens=truncated)
