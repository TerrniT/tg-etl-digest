from src.parsing.channels import parse_channels


def test_parse_basic_handles_dedupe():
    result = parse_channels("@durov durov https://t.me/durov", max_items=50)
    assert [str(h) for h in result.valid_handles] == ["durov"]
    assert result.invalid_tokens == []


def test_parse_mixed_multiline_and_invalid():
    raw = "@valid_name\nhttps://t.me/joinchat/AAAA\nabc t.me/hello_world"
    result = parse_channels(raw, max_items=50)
    assert [str(h) for h in result.valid_handles] == ["valid_name", "hello_world"]
    assert result.invalid_tokens == ["https://t.me/joinchat/AAAA", "abc"]


def test_parse_max_items_truncation():
    result = parse_channels("@alpha1 @alpha2 @alpha3", max_items=2)
    assert [str(h) for h in result.valid_handles] == ["alpha1", "alpha2"]
    assert result.truncated_tokens == ["@alpha3"]
