"""tests/test_summarize.py — Unit tests for tools/summarize.py"""

import pytest
from tools.summarize import summarize_ticket

_MAX = 300


class TestSummarizeTicket:
    def test_empty_string(self):
        assert summarize_ticket("") == ""

    def test_short_text_unchanged(self):
        text = "Please help me reset my password."
        result = summarize_ticket(text)
        assert result == text

    def test_strips_extra_whitespace(self):
        result = summarize_ticket("  Hello   world  ")
        assert result == "Hello world"

    def test_collapses_blank_lines(self):
        body = "Line one.\n\nLine two.\n\n\nLine three."
        result = summarize_ticket(body)
        assert "\n" not in result
        assert "Line one." in result
        assert "Line three." in result

    def test_long_text_truncated(self):
        long_body = "word " * 200  # ~1000 chars
        result = summarize_ticket(long_body)
        assert len(result) <= _MAX + 3  # allow for ellipsis

    def test_truncated_ends_with_ellipsis(self):
        long_body = "a" * 500
        result = summarize_ticket(long_body)
        assert result.endswith("...")

    def test_truncation_at_word_boundary(self):
        # Build text where word boundary is well within the first half of limit
        body = ("hello world " * 30).strip()  # 360 chars
        result = summarize_ticket(body)
        # Should not end mid-word (no partial word before "...")
        without_ellipsis = result[:-3]
        assert not without_ellipsis.endswith(" ")  # no trailing space
        assert " " not in without_ellipsis[-5:]  # last chars before ... are a full word

    def test_exactly_300_chars_not_truncated(self):
        text = "x" * _MAX
        result = summarize_ticket(text)
        assert len(result) == _MAX
        assert not result.endswith("...")
