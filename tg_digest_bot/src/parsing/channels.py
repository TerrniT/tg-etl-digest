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


def normalize_handle(raw: str) -> Optional[ChannelHandle]:
    token = (raw or "").strip()
    if not token:
        return None

    token = TRAILING_PUNCT_RE.sub("", token)
    token = token.strip()
    if not token:
        return None

    token = re.sub(r"^https?://", "", token, flags=re.IGNORECASE)

    if token.lower().startswith("t.me/"):
        token = token[5:]
    elif token.lower().startswith("telegram.me/"):
        token = token[12:]

    token = token.lstrip("@").strip()

    if not token:
        return None

    low = token.lower()
    if low.startswith("+") or low.startswith("joinchat"):
        return None

    if "/" in token:
        return None

    handle = low
    if not _is_valid_username(handle):
        return None

    return ChannelHandle(handle)


def parse_channels(text: str, *, max_items: int = 50) -> ParseChannelsResult:
    tokens = [t for t in SPLIT_RE.split((text or "").strip()) if t]

    valid: list[ChannelHandle] = []
    invalid: list[str] = []
    truncated: list[str] = []
    seen: set[str] = set()

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

    return ParseChannelsResult(valid_handles=valid, invalid_tokens=invalid, truncated_tokens=truncated)
