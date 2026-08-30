"""
tools/summarize.py — Condense a ticket body to ≤300 characters.

Used to produce a compact query string for similarity search and KB search,
avoiding hitting token limits or sending huge texts to subsequent tools.
"""

from __future__ import annotations

_MAX_CHARS = 300


def summarize_ticket(body: str) -> str:
    """
    Condense a ticket body to at most _MAX_CHARS characters.

    Strategy:
    1. Strip leading/trailing whitespace.
    2. Collapse multiple blank lines to a single newline.
    3. Truncate to _MAX_CHARS, adding an ellipsis if truncated.

    Args:
        body: Full ticket body text.

    Returns:
        A short string suitable for use as a search query.
    """
    if not body:
        return ""

    # Collapse excessive whitespace (newlines and multiple spaces)
    import re as _re
    lines = [line.strip() for line in body.splitlines()]
    joined = " ".join(line for line in lines if line)
    collapsed = _re.sub(r" {2,}", " ", joined)

    if len(collapsed) <= _MAX_CHARS:
        return collapsed

    # Truncate at a word boundary if possible
    truncated = collapsed[: _MAX_CHARS - 3]
    last_space = truncated.rfind(" ")
    if last_space > _MAX_CHARS // 2:
        truncated = truncated[:last_space]

    return truncated + "..."
