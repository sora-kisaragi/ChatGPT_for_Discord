from src.utils import chunk_message, format_response_text, validate_channel_access


def test_chunk_message_basic():
    text = "A" * 4500
    chunks = chunk_message(text, limit=2000)
    assert len(chunks) == 3
    assert len(chunks[0]) == 2000
    assert len(chunks[1]) == 2000
    assert len(chunks[2]) == 500


def test_format_response_text_newlines():
    text = "今日は晴れです。明日も晴れ。"
    formatted = format_response_text(text)
    assert "。\n" in formatted


def test_validate_channel_access():
    allowed = [1, 2, 3]
    assert validate_channel_access(2, allowed) is True
    assert validate_channel_access(5, allowed) is False
    assert validate_channel_access(10, []) is True  # empty means allow all
