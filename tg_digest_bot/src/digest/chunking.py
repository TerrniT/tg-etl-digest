from .assembler import DELIMITER


def chunk_text_for_telegram(text: str, *, max_len: int = 3500) -> list[str]:
    payload = (text or "").strip()
    if not payload:
        return []
    if len(payload) <= max_len:
        return [payload]

    parts = [p.strip() for p in payload.split(DELIMITER) if p.strip()]
    chunks: list[str] = []
    buf = ""

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

        start = 0
        while start < len(part):
            slice_ = part[start : start + max_len].strip()
            if slice_:
                chunks.append(slice_)
            start += max_len

    if buf.strip():
        chunks.append(buf.strip())

    return [chunk for chunk in chunks if chunk.strip()]
