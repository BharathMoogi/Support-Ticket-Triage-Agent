"""tests/test_classify.py — Unit tests for tools/classify.py"""

import pytest
from tools.classify import classify_ticket


class TestCategory:
    def test_billing_keywords(self):
        r = classify_ticket("Invoice question", "I was overcharged on my invoice this month")
        assert r["category"] == "billing"

    def test_account_keywords(self):
        r = classify_ticket("Login issue", "I cannot log in and my password reset is not working")
        assert r["category"] == "account"

    def test_technical_keywords(self):
        r = classify_ticket("App crash", "The app crashed with an error after the update")
        assert r["category"] == "technical"

    def test_feature_request_keywords(self):
        r = classify_ticket("Feature request", "I would love to see dark mode added")
        assert r["category"] == "feature_request"

    def test_general_fallback(self):
        r = classify_ticket("Hi", "Just wanted to say hello")
        assert r["category"] == "general"


class TestPriority:
    def test_p1_urgent(self):
        r = classify_ticket("URGENT", "We have an outage and data loss is occurring")
        assert r["priority"] == "P1"

    def test_p2_blocker(self):
        r = classify_ticket("Blocker", "Cannot complete the workflow, it is broken")
        assert r["priority"] == "P2"

    def test_p3_intermittent(self):
        r = classify_ticket("Slow", "The dashboard is sometimes slow")
        assert r["priority"] == "P3"

    def test_p4_question(self):
        r = classify_ticket("Question", "How do I export my data?")
        assert r["priority"] == "P4"

    def test_default_priority_p3(self):
        r = classify_ticket("General inquiry", "Just checking something")
        assert r["priority"] == "P3"


class TestSentiment:
    def test_frustrated(self):
        r = classify_ticket("Fed up", "This is absolutely ridiculous and outrageous")
        assert r["sentiment"] == "frustrated"

    def test_negative(self):
        r = classify_ticket("Disappointed", "I am very disappointed with the poor service")
        assert r["sentiment"] == "negative"

    def test_positive(self):
        r = classify_ticket("Thanks!", "Just wanted to say thank you, excellent support")
        assert r["sentiment"] == "positive"

    def test_neutral_fallback(self):
        r = classify_ticket("Info", "I would like some information about my account")
        assert r["sentiment"] == "neutral"


class TestReturnSchema:
    def test_always_returns_three_keys(self):
        r = classify_ticket("x", "x")
        assert set(r.keys()) == {"category", "priority", "sentiment"}

    def test_values_are_strings(self):
        r = classify_ticket("test", "test body text")
        assert all(isinstance(v, str) for v in r.values())
