"""
tools/similar.py — Find historically similar resolved tickets using TF-IDF keyword overlap.

Reads from data/tickets.jsonl (one JSON object per line).
No vector database or embedding model required — swap-able later.
"""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from pathlib import Path

# Default path relative to project root (overridable via env var for tests)
_DATA_FILE = Path(os.getenv("TICKETS_DATA_FILE", "data/tickets.jsonl"))

# Simple English stop-words to ignore during TF-IDF
_STOP_WORDS = frozenset(
    "a an the and or but in on at to for of with is are was were be been "
    "being have has had do does did will would could should may might "
    "i me my we our you your he she it its they their this that these "
    "those what which who whom when where why how not no".split()
)


def _tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, remove stop-words."""
    tokens = re.findall(r"[a-z]+", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


def _load_tickets() -> list[dict]:
    """Load all tickets from the JSONL data file."""
    if not _DATA_FILE.exists():
        return []
    tickets = []
    with _DATA_FILE.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                tickets.append(json.loads(line))
    return tickets


def _tf(tokens: list[str]) -> dict[str, float]:
    counts = Counter(tokens)
    total = max(len(tokens), 1)
    return {term: count / total for term, count in counts.items()}


def _idf(term: str, corpus: list[list[str]]) -> float:
    containing = sum(1 for doc in corpus if term in doc)
    if containing == 0:
        return 0.0
    return math.log((1 + len(corpus)) / (1 + containing)) + 1


def _tfidf_score(query_tokens: list[str], doc_tokens: list[str],
                 corpus: list[list[str]]) -> float:
    """Cosine-like TF-IDF overlap score between query and a document."""
    if not query_tokens or not doc_tokens:
        return 0.0
    doc_tf = _tf(doc_tokens)
    score = 0.0
    for term in set(query_tokens):
        if term in doc_tf:
            idf = _idf(term, corpus)
            score += doc_tf[term] * idf
    return score


def find_similar(query: str, top_k: int = 3) -> list[dict]:
    """
    Find the most similar historical tickets to the given query.

    Args:
        query: Short text describing the current ticket (use summarize_ticket output).
        top_k: Maximum number of results to return (capped at 5).

    Returns:
        List of ticket dicts (id, subject, body snippet, resolution) sorted by
        similarity score descending.
    """
    top_k = min(max(int(top_k), 1), 5)
    tickets = _load_tickets()
    if not tickets:
        return []

    query_tokens = _tokenize(query)

    # Build corpus of tokenised ticket texts for IDF calculation
    corpus: list[list[str]] = [
        _tokenize(f"{t.get('subject', '')} {t.get('body', '')}")
        for t in tickets
    ]

    scored: list[tuple[float, dict]] = []
    for ticket, doc_tokens in zip(tickets, corpus):
        score = _tfidf_score(query_tokens, doc_tokens, corpus)
        if score > 0:
            scored.append((score, ticket))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _, ticket in scored[:top_k]:
        results.append(
            {
                "id": ticket.get("id", ""),
                "subject": ticket.get("subject", ""),
                "body_snippet": ticket.get("body", "")[:200],
                "resolution": ticket.get("resolution", "No resolution recorded."),
                "category": ticket.get("category", ""),
            }
        )
    return results
