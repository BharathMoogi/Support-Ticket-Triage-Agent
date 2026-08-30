"""
tools/knowledge.py — Search the internal knowledge base for relevant help articles.

Reads from data/kb_articles.json (list of article objects).
Uses the same TF-IDF token overlap approach as similar.py.
"""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from pathlib import Path

_DATA_FILE = Path(os.getenv("KB_DATA_FILE", "data/kb_articles.json"))

_STOP_WORDS = frozenset(
    "a an the and or but in on at to for of with is are was were be been "
    "being have has had do does did will would could should may might "
    "i me my we our you your he she it its they their this that these "
    "those what which who whom when where why how not no".split()
)


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z]+", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


def _load_articles() -> list[dict]:
    if not _DATA_FILE.exists():
        return []
    with _DATA_FILE.open(encoding="utf-8") as fh:
        return json.load(fh)


def _score(query_tokens: list[str], article: dict) -> float:
    """Simple token overlap score (Jaccard-like)."""
    text = f"{article.get('title', '')} {article.get('content', '')} {' '.join(article.get('tags', []))}"
    article_tokens = set(_tokenize(text))
    query_set = set(query_tokens)
    if not query_set or not article_tokens:
        return 0.0
    intersection = query_set & article_tokens
    union = query_set | article_tokens
    return len(intersection) / len(union)


def search_knowledge_base(query: str) -> list[dict]:
    """
    Search KB articles by keyword overlap.

    Args:
        query: Search terms derived from the ticket (subject + summary).

    Returns:
        Up to 3 most relevant articles, each with id, title, excerpt, url.
    """
    articles = _load_articles()
    if not articles:
        return []

    query_tokens = _tokenize(query)
    scored = [((_score(query_tokens, a)), a) for a in articles]
    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, article in scored[:3]:
        if score == 0:
            break
        results.append(
            {
                "id": article.get("id", ""),
                "title": article.get("title", ""),
                "excerpt": article.get("content", "")[:300],
                "url": article.get("url", ""),
                "tags": article.get("tags", []),
            }
        )
    return results
