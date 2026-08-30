"""
agent/run.py — The core agentic loop for the Ticket Triage Agent.

Orchestrates a single Claude run for one ticket:
1. Sends the ticket to Claude with the tool schemas.
2. Dispatches tool_use blocks to the local tool registry.
3. Logs every tool call + result + model text to the trajectory.
4. Extracts the final text reply and enqueues it for human review.

Never calls any external send API — the draft stays in the review queue.
"""

from __future__ import annotations

import json
import os
from typing import Any

import anthropic
from dotenv import load_dotenv

from agent.prompts import SYSTEM_PROMPT, TOOLS
from agent.review_queue import enqueue
from agent.trajectory import TrajectoryLogger
from tools import TOOL_REGISTRY

load_dotenv()

_DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
_MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
_MAX_ITERATIONS = 20  # safety cap — prevents infinite tool loops


def _make_ticket_message(ticket: dict) -> str:
    """Format a ticket dict into the user message content."""
    lines = [
        f"**Ticket ID**: {ticket.get('id', 'UNKNOWN')}",
        f"**Subject**: {ticket.get('subject', '(no subject)')}",
        f"**From**: {ticket.get('from', 'customer@example.com')}",
        f"**Created**: {ticket.get('created_at', 'unknown')}",
        "",
        "**Body**:",
        ticket.get("body", "(no body)"),
    ]
    if ticket.get("metadata"):
        lines += ["", f"**Metadata**: {json.dumps(ticket['metadata'])}"]
    return "\n".join(lines)


def run_triage(ticket: dict) -> dict[str, str]:
    """
    Run the full triage agent for a single ticket.

    Args:
        ticket: Dict with keys: id, subject, body, and optionally
                from, created_at, metadata.

    Returns:
        {
            "ticket_id": str,
            "draft_reply": str,
            "trajectory_path": str,
            "queue_path": str,
        }

    Raises:
        ValueError: If the ticket is missing required fields.
        RuntimeError: If the agent loop exceeds _MAX_ITERATIONS.
    """
    ticket_id = ticket.get("id")
    if not ticket_id:
        raise ValueError("Ticket must have an 'id' field.")
    subject = ticket.get("subject", "(no subject)")

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    logger = TrajectoryLogger(ticket_id=ticket_id)

    # Build initial conversation
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": _make_ticket_message(ticket)},
    ]

    draft_reply: str = ""
    classification: dict = {}
    iteration = 0

    while iteration < _MAX_ITERATIONS:
        iteration += 1

        response = client.messages.create(
            model=_DEFAULT_MODEL,
            max_tokens=_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Log any text blocks (Claude's reasoning / commentary)
        for block in response.content:
            if block.type == "text":
                logger.log_model_text(block.text)
                # The last substantial text block is the draft reply
                if len(block.text.strip()) > 20:
                    draft_reply = block.text.strip()

        # If Claude is done (no tool use), exit the loop
        if response.stop_reason == "end_turn":
            break

        # Collect all tool use blocks and process them
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_use_blocks:
            break  # no tools requested and not end_turn — treat as done

        # Append Claude's response to the conversation history
        messages.append({"role": "assistant", "content": response.content})

        # Build the tool results list for this round
        tool_results: list[dict[str, Any]] = []
        for block in tool_use_blocks:
            tool_name = block.name
            tool_input = block.input

            logger.log_tool_call(tool_name, tool_input)

            # Dispatch to local tool
            func = TOOL_REGISTRY.get(tool_name)
            if func is None:
                result = {"error": f"Unknown tool: {tool_name}"}
            else:
                try:
                    result = func(**tool_input)
                except Exception as exc:  # noqa: BLE001
                    result = {"error": str(exc)}

            logger.log_tool_result(tool_name, result)

            # Capture classification for the queue record
            if tool_name == "classify_ticket" and isinstance(result, dict):
                classification = result

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                }
            )

        # Feed all results back to Claude in one turn
        messages.append({"role": "user", "content": tool_results})

    else:
        raise RuntimeError(
            f"Agent loop exceeded {_MAX_ITERATIONS} iterations for ticket {ticket_id}."
        )

    trajectory_path = logger.close()

    # Enqueue the draft for human review — no external send
    queue_path = enqueue(
        ticket_id=ticket_id,
        subject=subject,
        draft_reply=draft_reply,
        classification=classification,
        trajectory_path=trajectory_path,
    )

    return {
        "ticket_id": ticket_id,
        "draft_reply": draft_reply,
        "trajectory_path": trajectory_path,
        "queue_path": queue_path,
    }
