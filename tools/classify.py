"""
tools/classify.py — Classify a support ticket using keyword heuristics.

Returns a dict with:
    category  : str  (e.g. "billing", "technical", "account", "general")
    priority  : str  ("P1" | "P2" | "P3" | "P4")
    sentiment : str  ("positive" | "neutral" | "negative" | "frustrated")
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Category keyword mapping  (order matters — first match wins)
# ---------------------------------------------------------------------------
_CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("billing", ["invoice", "charge", "refund", "payment", "billing", "subscription",
                 "price", "cost", "fee", "credit card", "overcharged"]),
    ("account", ["login", "password", "account", "sign in", "locked", "access",
                 "two-factor", "2fa", "email change", "username"]),
    ("technical", ["error", "bug", "crash", "not working", "broken", "issue",
                   "failed", "exception", "500", "timeout", "slow", "lag",
                   "install", "update", "upgrade"]),
    ("feature_request", ["feature", "request", "suggest", "would love", "wish",
                         "enhancement", "improvement", "add support for"]),
    ("general", []),  # catch-all
]

# ---------------------------------------------------------------------------
# Priority keyword mapping  (P1 = urgent, P4 = low)
# ---------------------------------------------------------------------------
_PRIORITY_RULES: list[tuple[str, list[str]]] = [
    ("P1", ["urgent", "asap", "critical", "down", "outage", "data loss",
            "security", "breach", "immediately", "emergency"]),
    ("P2", ["important", "blocker", "blocking", "cannot", "can't", "unable",
            "broken", "not working", "failed"]),
    ("P3", ["slow", "intermittent", "sometimes", "occasionally", "minor bug"]),
    ("P4", ["question", "how to", "wondering", "feature request", "suggestion",
            "feedback", "when will"]),
]

# ---------------------------------------------------------------------------
# Sentiment keyword mapping
# ---------------------------------------------------------------------------
_SENTIMENT_RULES: list[tuple[str, list[str]]] = [
    ("frustrated", ["frustrated", "unacceptable", "terrible", "awful", "disgusted",
                    "ridiculous", "outrageous", "fed up", "worst", "furious"]),
    ("negative",   ["disappointed", "unhappy", "not happy", "poor", "bad",
                    "useless", "annoyed", "problem", "issue"]),
    ("positive",   ["thanks", "thank you", "appreciate", "great", "love",
                    "excellent", "happy", "pleased", "awesome"]),
    ("neutral",    []),  # catch-all
]


def _match(text: str, keywords: list[str]) -> bool:
    """Return True if any keyword appears in the lowercased text."""
    lower = text.lower()
    return any(kw in lower for kw in keywords)


def classify_ticket(subject: str, body: str) -> dict[str, str]:
    """
    Classify a support ticket.

    Args:
        subject: Ticket subject line.
        body: Full ticket body text.

    Returns:
        {"category": str, "priority": str, "sentiment": str}
    """
    combined = f"{subject} {body}"

    # Category
    category = "general"
    for cat, keywords in _CATEGORY_RULES:
        if not keywords or _match(combined, keywords):
            category = cat
            break

    # Priority
    priority = "P3"
    for pri, keywords in _PRIORITY_RULES:
        if keywords and _match(combined, keywords):
            priority = pri
            break

    # Sentiment
    sentiment = "neutral"
    for sent, keywords in _SENTIMENT_RULES:
        if not keywords or _match(combined, keywords):
            sentiment = sent
            break

    return {"category": category, "priority": priority, "sentiment": sentiment}
