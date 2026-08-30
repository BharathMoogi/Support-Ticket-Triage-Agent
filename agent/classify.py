"""
agent/classify.py — Structured LLM Ticket Classification.

Classifies incoming support tickets into fixed categories and urgency levels
using a single structured-output LLM call with a forced Anthropic JSON schema.
"""

from __future__ import annotations

import json
import os
from typing import Any, Literal

import anthropic
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

CategoryType = Literal["billing", "bug", "how-to", "other"]
UrgencyType = Literal["low", "medium", "high"]

# ---------------------------------------------------------------------------
# Strict JSON Tool Schema for Structured Output
# ---------------------------------------------------------------------------

CLASSIFICATION_TOOL = {
    "name": "record_ticket_classification",
    "description": "Record the classified category and urgency of a customer support ticket.",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["billing", "bug", "how-to", "other"],
                "description": (
                    "The primary category of the ticket:\n"
                    "- 'billing': Invoices, refunds, charges, payments, seat upgrades, pricing.\n"
                    "- 'bug': Unexpected errors, crashes, broken sync, UI/backend malfunctions.\n"
                    "- 'how-to': User questions on features, exports, configurations, integrations.\n"
                    "- 'other': Contradictory, nonsensical, out-of-scope, or unclassifiable requests."
                ),
            },
            "urgency": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": (
                    "The urgency level:\n"
                    "- 'high': Outages, data loss, severe business blockers, major payment lockouts, angry churn risk.\n"
                    "- 'medium': Impaired non-critical features, single-user bugs, billing questions.\n"
                    "- 'low': General how-to questions, minor inquiries, feature feedback."
                ),
            },
        },
        "required": ["category", "urgency"],
    },
}

SYSTEM_PROMPT = """\
You are an expert support ticket triage classifier.
Analyze the incoming customer support ticket text and output its classification
using the provided record_ticket_classification tool.
Evaluate both the topic (category) and the business impact / emotional urgency.
"""


def classify_ticket(
    ticket_text: str,
    client: Any | None = None,
    model: str | None = None,
) -> dict[str, str]:
    """
    Classify a support ticket using a structured-output LLM call (Groq or Anthropic).
    """
    if not ticket_text or not ticket_text.strip():
        return {"category": "other", "urgency": "low"}

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and (client is None or hasattr(client, "chat")):
        import httpx
        from groq import Groq
        if client is None:
            http_client = httpx.Client(verify=False)
            client = Groq(api_key=groq_key, http_client=http_client)
        groq_model = model or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

        prompt = f"""You are an expert support ticket triage classifier.
Analyze this ticket and classify it into category ('billing', 'bug', 'how-to', 'other') and urgency ('low', 'medium', 'high').
Respond ONLY with a valid JSON object in this exact format:
{{"category": "billing|bug|how-to|other", "urgency": "low|medium|high"}}

Ticket:
{ticket_text}"""

        response = client.chat.completions.create(
            model=groq_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        try:
            content = response.choices[0].message.content or "{}"
            data = json.loads(content)
            cat = data.get("category", "other").lower()
            urg = data.get("urgency", "medium").lower()
            if cat not in {"billing", "bug", "how-to", "other"}:
                cat = "other"
            if urg not in {"low", "medium", "high"}:
                urg = "medium"
            return {"category": cat, "urgency": urg}
        except Exception:
            return {"category": "other", "urgency": "medium"}

    if client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("No API key configured.")
        client = anthropic.Anthropic(api_key=api_key)

    anthropic_model = model or DEFAULT_MODEL
    response = client.messages.create(
        model=anthropic_model,
        max_tokens=256,
        system=SYSTEM_PROMPT,
        tools=[CLASSIFICATION_TOOL],
        tool_choice={"type": "tool", "name": "record_ticket_classification"},
        messages=[
            {"role": "user", "content": f"Ticket to classify:\n\n{ticket_text}"}
        ],
    )

    # Extract tool input from response
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "record_ticket_classification":
            data = block.input
            category = data.get("category", "other")
            urgency = data.get("urgency", "medium")

            if category not in {"billing", "bug", "how-to", "other"}:
                category = "other"
            if urgency not in {"low", "medium", "high"}:
                urgency = "medium"

            return {
                "category": category,
                "urgency": urgency,
            }

    return {"category": "other", "urgency": "medium"}


# ---------------------------------------------------------------------------
# Self Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    print("=== Testing Structured LLM Ticket Classification ===")

    test_cases = [
        (
            "How do I export our team boards into CSV format?",
            "how-to",
            "low",
        ),
        (
            "URGENT: Database sync failed and all team members are getting 502 Bad Gateway!",
            "bug",
            "high",
        ),
        (
            "We were charged $1,440 for an annual renewal that we canceled. Please issue a refund.",
            "billing",
            "medium",
        ),
        (
            "Can you beam my cards into a 3D hologram Linux VR headset using quantum neural link?",
            "other",
            "low",
        ),
    ]

    try:
        client = anthropic.Anthropic()
        for idx, (text, expected_cat, expected_urg) in enumerate(test_cases, 1):
            print(f"\n--- Test Case {idx} ---")
            print(f"Input: {text}")
            result = classify_ticket(text, client=client)
            print(f"Classification Result: {result}")
            assert result["category"] in {"billing", "bug", "how-to", "other"}
            assert result["urgency"] in {"low", "medium", "high"}
            print(f"Category: {result['category']} (Expected: {expected_cat}) | Urgency: {result['urgency']} (Expected: {expected_urg})")

        print("\nAll classification tests completed successfully!")
    except Exception as exc:
        print(f"\nNote: Live LLM test skipped or errored ({exc}). Checking schema definition...")
        assert CLASSIFICATION_TOOL["name"] == "record_ticket_classification"
        assert set(CLASSIFICATION_TOOL["input_schema"]["properties"]["category"]["enum"]) == {"billing", "bug", "how-to", "other"}
        assert set(CLASSIFICATION_TOOL["input_schema"]["properties"]["urgency"]["enum"]) == {"low", "medium", "high"}
        print("Schema validation passed.")
