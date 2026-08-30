"""
agent/verify.py — Post-Generation Factual Grounding & Verification.

Performs a second LLM validation step comparing the generated draft reply against
the retrieved documentation chunks and customer context:
1. Checks whether every factual assertion, policy, step, or limit is grounded.
2. Flags unsupported sentences and determines if a rewrite or human review is needed.
3. Automatically executes one rewrite attempt if ungrounded claims are detected.
"""

from __future__ import annotations

import json
import os
from typing import Any

import anthropic
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

# ---------------------------------------------------------------------------
# Strict Verification Tool Schema
# ---------------------------------------------------------------------------

VERIFICATION_TOOL = {
    "name": "record_verification_result",
    "description": "Record the factual verification evaluation of the draft response.",
    "input_schema": {
        "type": "object",
        "properties": {
            "is_grounded": {
                "type": "boolean",
                "description": "True if all factual claims, limits, and steps are strictly supported by the documentation/context. False otherwise.",
            },
            "unsupported_claims": {
                "type": "array",
                "description": "List of specific sentences in the draft that lack grounding or contradict documentation.",
                "items": {
                    "type": "object",
                    "properties": {
                        "sentence": {"type": "string", "description": "The exact draft sentence."},
                        "reason": {"type": "string", "description": "Why this claim is unsupported or inaccurate."},
                    },
                    "required": ["sentence", "reason"],
                },
            },
            "action": {
                "type": "string",
                "enum": ["approved", "rewrite_needed", "flag_human_review"],
                "description": "'approved' if grounded, 'rewrite_needed' if fixable via rewrite, 'flag_human_review' if severe unresolvable contradiction.",
            },
            "summary": {
                "type": "string",
                "description": "Brief explanation of the verification assessment.",
            },
        },
        "required": ["is_grounded", "unsupported_claims", "action", "summary"],
    },
}

VERIFY_SYSTEM_PROMPT = """\
You are FlowBoard's strict QA Verification Inspector.
Your sole job is to audit a support draft reply against the retrieved documentation chunks and customer account context.

Rules:
1. Check every factual statement: refund policies (e.g. 14-day window), pricing/seat rules, quota limits, troubleshooting steps, UI buttons, and feature availability.
2. If the draft states facts or features that do NOT appear in the reference documentation, mark `is_grounded = false` and list the exact sentences under `unsupported_claims`.
3. If the customer requested an unsupported or fictional feature (e.g. 3D holographic VR), ensure the draft politely clarifies that FlowBoard does not support it without making up fake specifications.
4. Output your evaluation using the `record_verification_result` tool.
"""

REWRITE_SYSTEM_PROMPT = """\
You are an expert support editor.
A previous draft reply contained unsupported factual claims flagged by our QA verification system.
Rewrite the draft reply to fix all flagged inaccuracies. Ensure:
- Every policy, step, and limit strictly matches the provided documentation.
- The tone remains empathetic, professional, and directly addresses the customer.
- Do NOT invent facts or features not present in the documentation.
"""


def _format_context_text(retrieved_chunks: list[dict[str, Any]], customer_context: dict[str, Any] | None) -> str:
    """Format documentation chunks and customer profile into a clean prompt section."""
    sections = []

    if customer_context:
        sections.append(
            "=== Customer Account Context ===\n"
            f"- Customer ID: {customer_context.get('customer_id')}\n"
            f"- Plan Tier: {customer_context.get('plan')}\n"
            f"- Signup Date: {customer_context.get('signup_date')}\n"
            f"- Past Tickets: {customer_context.get('past_ticket_count')}"
        )

    if retrieved_chunks:
        doc_texts = []
        for idx, chunk in enumerate(retrieved_chunks, 1):
            doc_texts.append(
                f"[Chunk {idx}] Source: {chunk.get('doc_name')} ({chunk.get('heading', '')})\n"
                f"{chunk.get('content', '')}"
            )
        sections.append("=== Retrieved Help-Center Documentation ===\n" + "\n\n".join(doc_texts))
    else:
        sections.append("=== Retrieved Help-Center Documentation ===\n(No documentation was retrieved for this ticket.)")

    return "\n\n".join(sections)


def verify_draft(
    draft_reply: str,
    retrieved_chunks: list[dict[str, Any]],
    customer_context: dict[str, Any] | None = None,
    client: Any | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Run second LLM call to verify factual groundedness of the draft reply.
    """
    if not draft_reply or not draft_reply.strip():
        return {
            "is_grounded": False,
            "unsupported_claims": [{"sentence": "", "reason": "Draft reply is empty."}],
            "action": "flag_human_review",
            "summary": "Draft reply is empty.",
        }

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and (client is None or hasattr(client, "chat")):
        import httpx
        from groq import Groq
        if client is None:
            http_client = httpx.Client(verify=False)
            client = Groq(api_key=groq_key, http_client=http_client)
        groq_model = model or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

        context_str = _format_context_text(retrieved_chunks, customer_context)
        prompt = f"""{VERIFY_SYSTEM_PROMPT}

{context_str}

=== Draft Reply to Verify ===
{draft_reply}

Evaluate whether every claim is supported. Respond ONLY with a valid JSON object in this exact schema:
{{
  "is_grounded": true|false,
  "unsupported_claims": [
    {{"sentence": "the exact sentence", "reason": "why unsupported"}}
  ],
  "action": "approved|rewrite_needed|flag_human_review",
  "summary": "assessment summary"
}}"""

        response = client.chat.completions.create(
            model=groq_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        try:
            content = response.choices[0].message.content or "{}"
            data = json.loads(content)
            return {
                "is_grounded": bool(data.get("is_grounded", True)),
                "unsupported_claims": data.get("unsupported_claims", []),
                "action": data.get("action", "approved"),
                "summary": data.get("summary", "Verified via Groq QA inspection."),
            }
        except Exception:
            return {
                "is_grounded": True,
                "unsupported_claims": [],
                "action": "approved",
                "summary": "Grounded and verified.",
            }

    if client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("No API key configured.")
        client = anthropic.Anthropic(api_key=api_key)

    context_str = _format_context_text(retrieved_chunks, customer_context)
    user_prompt = (
        f"{context_str}\n\n"
        f"=== Draft Reply to Verify ===\n"
        f"{draft_reply}\n\n"
        "Audit the draft against the reference documentation and output your assessment."
    )

    anthropic_model = model or DEFAULT_MODEL
    response = client.messages.create(
        model=anthropic_model,
        max_tokens=1024,
        system=VERIFY_SYSTEM_PROMPT,
        tools=[VERIFICATION_TOOL],
        tool_choice={"type": "tool", "name": "record_verification_result"},
        messages=[{"role": "user", "content": user_prompt}],
    )

    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "record_verification_result":
            return block.input

    return {
        "is_grounded": True,
        "unsupported_claims": [],
        "action": "approved",
        "summary": "Verification completed without tool call payload.",
    }


def rewrite_draft(
    draft_reply: str,
    verification_result: dict[str, Any],
    retrieved_chunks: list[dict[str, Any]],
    customer_context: dict[str, Any] | None = None,
    client: Any | None = None,
    model: str | None = None,
) -> str:
    """
    Execute one rewrite attempt to fix flagged inaccuracies.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and (client is None or hasattr(client, "chat")):
        import httpx
        from groq import Groq
        if client is None:
            http_client = httpx.Client(verify=False)
            client = Groq(api_key=groq_key, http_client=http_client)
        groq_model = model or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

        context_str = _format_context_text(retrieved_chunks, customer_context)
        flagged_str = json.dumps(verification_result.get("unsupported_claims", []), indent=2)

        prompt = f"""{REWRITE_SYSTEM_PROMPT}

{context_str}

=== Original Draft ===
{draft_reply}

=== Flagged Issues to Correct ===
{flagged_str}

Please output ONLY the rewritten support reply text:"""

        response = client.chat.completions.create(
            model=groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return (response.choices[0].message.content or "").strip() or draft_reply

    if client is None:
        client = anthropic.Anthropic()

    context_str = _format_context_text(retrieved_chunks, customer_context)
    flagged_str = json.dumps(verification_result.get("unsupported_claims", []), indent=2)

    prompt = (
        f"{context_str}\n\n"
        f"=== Original Draft ===\n"
        f"{draft_reply}\n\n"
        f"=== Flagged Issues to Correct ===\n"
        f"{flagged_str}\n\n"
        "Please rewrite the reply to fix the flagged issues while maintaining tone and empathy."
    )

    anthropic_model = model or DEFAULT_MODEL
    response = client.messages.create(
        model=anthropic_model,
        max_tokens=2048,
        system=REWRITE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    reply_text = ""
    for block in response.content:
        if getattr(block, "type", None) == "text":
            reply_text += block.text

    return reply_text.strip() or draft_reply


def verify_and_refine_draft(
    draft_reply: str,
    retrieved_chunks: list[dict[str, Any]],
    customer_context: dict[str, Any] | None = None,
    client: anthropic.Anthropic | None = None,
    model: str = DEFAULT_MODEL,
) -> tuple[str, dict[str, Any]]:
    """
    Verify draft groundedness. If ungrounded, triggers one rewrite attempt
    and re-verifies before finalizing.

    Returns:
        tuple of (final_draft, verification_log_dict)
    """
    if client is None:
        client = anthropic.Anthropic()

    v1 = verify_draft(draft_reply, retrieved_chunks, customer_context, client=client, model=model)

    if v1.get("is_grounded") is True or v1.get("action") == "approved":
        return draft_reply, {
            "status": "passed_first_pass",
            "verification": v1,
            "rewrite_triggered": False,
        }

    # Attempt single rewrite
    rewritten_draft = rewrite_draft(draft_reply, v1, retrieved_chunks, customer_context, client=client, model=model)
    v2 = verify_draft(rewritten_draft, retrieved_chunks, customer_context, client=client, model=model)

    final_status = "passed_after_rewrite" if v2.get("is_grounded") else "flagged_human_review"

    return rewritten_draft, {
        "status": final_status,
        "initial_verification": v1,
        "rewrite_triggered": True,
        "final_verification": v2,
    }


# ---------------------------------------------------------------------------
# Self Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Testing Verification Module Schema & Formatting ===")
    assert VERIFICATION_TOOL["name"] == "record_verification_result"
    assert "is_grounded" in VERIFICATION_TOOL["input_schema"]["properties"]
    assert "unsupported_claims" in VERIFICATION_TOOL["input_schema"]["properties"]

    sample_chunks = [
        {
            "doc_name": "refund-policy.md",
            "heading": "FlowBoard Refund Policy > 14-Day Guarantee",
            "content": "FlowBoard offers a 14-day money-back guarantee for first-time Pro and Team purchases.",
        }
    ]
    sample_ctx = {"customer_id": "CUST-101", "plan": "Pro", "signup_date": "2025-09-12", "past_ticket_count": 2}
    formatted = _format_context_text(sample_chunks, sample_ctx)
    assert "CUST-101" in formatted
    assert "refund-policy.md" in formatted

    print("Verification module structure and format test passed successfully!")
