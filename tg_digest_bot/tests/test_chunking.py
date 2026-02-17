from src.digest.assembler import DELIMITER
from src.digest.chunking import chunk_text_for_telegram


def test_chunking_short():
    chunks = chunk_text_for_telegram("hello", max_len=10)
    assert chunks == ["hello"]


def test_chunking_by_blocks():
    text = DELIMITER.join(["block1", "block2", "block3"])
    chunks = chunk_text_for_telegram(text, max_len=20)
    assert all(len(chunk) <= 20 for chunk in chunks)
    assert chunks == ["block1", "block2", "block3"]


def test_chunking_long_single_block():
    text = "a" * 95
    chunks = chunk_text_for_telegram(text, max_len=30)
    assert all(0 < len(chunk) <= 30 for chunk in chunks)
    assert "".join(chunks) == text
