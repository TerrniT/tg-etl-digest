# FILE: src/digest/chunking.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Split digest text into Telegram-safe chunks while preserving block structure when possible.
#   SCOPE: Chunk by digest delimiter first, then fallback to hard slicing oversized blocks.
#   DEPENDS: M-DIGEST-ASSEMBLER
#   LINKS: docs/development-plan.xml#M-DIGEST-CHUNKING, docs/knowledge-graph.xml#M-DIGEST-CHUNKING
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   chunk_text_for_telegram — Produce ordered chunks that fit Telegram message length limits.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE contracts and semantic block markers.
# END_CHANGE_SUMMARY

from .assembler import DELIMITER


# START_CONTRACT: chunk_text_for_telegram
#   PURPOSE: Chunk digest text for Telegram transport without dropping semantic content.
#   INPUTS: { text: str - digest raw text, max_len: int - hard maximum per message }
#   OUTPUTS: { list[str] - ordered chunk list within max_len constraints }
#   SIDE_EFFECTS: none
#   LINKS: M-DIGEST-CHUNKING, M-DIGEST-ASSEMBLER
# END_CONTRACT: chunk_text_for_telegram
def chunk_text_for_telegram(text: str, *, max_len: int = 3500) -> list[str]:
    # START_BLOCK_VALIDATE_PAYLOAD_AND_FAST_PATH
    payload = (text or "").strip()
    if not payload:
        return []
    if len(payload) <= max_len:
        return [payload]
    # END_BLOCK_VALIDATE_PAYLOAD_AND_FAST_PATH

    # START_BLOCK_PREPARE_BLOCK_SPLIT_STATE
    parts = [p.strip() for p in payload.split(DELIMITER) if p.strip()]
    chunks: list[str] = []
    buf = ""
    # END_BLOCK_PREPARE_BLOCK_SPLIT_STATE

    # START_BLOCK_ACCUMULATE_OR_FLUSH_BLOCKS
    for part in parts:
        candidate = part if not buf else f"{buf}{DELIMITER}{part}"
        if len(candidate) <= max_len:
            buf = candidate
            continue

        if buf:
            chunks.append(buf)
            buf = ""

        if len(part) <= max_len:
            buf = part
            continue

        # START_BLOCK_HARD_SLICE_OVERSIZED_BLOCK
        start = 0
        while start < len(part):
            slice_ = part[start : start + max_len].strip()
            if slice_:
                chunks.append(slice_)
            start += max_len
        # END_BLOCK_HARD_SLICE_OVERSIZED_BLOCK
    # END_BLOCK_ACCUMULATE_OR_FLUSH_BLOCKS

    # START_BLOCK_FINALIZE_AND_FILTER_CHUNKS
    if buf.strip():
        chunks.append(buf.strip())

    return [chunk for chunk in chunks if chunk.strip()]
    # END_BLOCK_FINALIZE_AND_FILTER_CHUNKS
