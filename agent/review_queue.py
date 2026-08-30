"""
agent/review_queue.py — File-Based Human Review Queue.

Writes finished (verified) drafts to /agent/review_queue/{ticket_id}.json
with status "pending_review".
Nothing in this codebase calls any external email/send API.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

DEFAULT_QUEUE_DIR = Path(os.getenv("AGENT_REVIEW_QUEUE_DIR", "agent/review_queue"))

ReviewStatus = Literal["pending_review", "approved", "edited", "rejected"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_to_review_queue(
    *,
    ticket_id: str,
    customer_id: str = "UNKNOWN",
    subject: str = "(No Subject)",
    draft_reply: str,
    verification_info: dict[str, Any] | None = None,
    trajectory_path: str = "",
    queue_dir: str | Path = DEFAULT_QUEUE_DIR,
) -> Path:
    """
    Save a verified draft reply into the review queue JSON file.

    Args:
        ticket_id: Unique ticket ID (e.g. 'TKT-001').
        customer_id: Customer identifier.
        subject: Ticket subject line.
        draft_reply: The verified draft text.
        verification_info: Summary of verification results.
        trajectory_path: Relative or absolute path to trajectory JSON.
        queue_dir: Target directory for review JSON files.

    Returns:
        Path to the saved review JSON file.
    """
    target_dir = Path(queue_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    file_path = target_dir / f"{ticket_id.upper()}.json"

    record: dict[str, Any] = {
        "ticket_id": ticket_id.upper(),
        "customer_id": customer_id,
        "subject": subject,
        "draft_reply": draft_reply,
        "verification_info": verification_info or {},
        "status": "pending_review",
        "queued_at": _now(),
        "reviewed_at": None,
        "reviewer_decision": None,
        "edited_reply": None,
        "trajectory_path": str(trajectory_path),
    }

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    return file_path


def list_review_queue(
    queue_dir: str | Path = DEFAULT_QUEUE_DIR,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """List all review queue items, optionally filtered by status."""
    target_dir = Path(queue_dir)
    if not target_dir.exists():
        return []

    items = []
    for file in sorted(target_dir.glob("*.json")):
        try:
            with file.open(encoding="utf-8") as f:
                data = json.load(f)
                if status is None or data.get("status") == status:
                    items.append(data)
        except Exception:
            continue

    return items


def load_review_item(ticket_id: str, queue_dir: str | Path = DEFAULT_QUEUE_DIR) -> dict[str, Any] | None:
    """Load a specific review item by ticket ID."""
    file_path = Path(queue_dir) / f"{ticket_id.upper()}.json"
    if not file_path.exists():
        return None
    with file_path.open(encoding="utf-8") as f:
        return json.load(f)


def update_review_decision(
    ticket_id: str,
    decision: ReviewStatus,
    edited_reply: str | None = None,
    queue_dir: str | Path = DEFAULT_QUEUE_DIR,
) -> dict[str, Any]:
    """
    Update human reviewer decision ('approved' | 'edited' | 'rejected') on a review item.
    """
    file_path = Path(queue_dir) / f"{ticket_id.upper()}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Review file {file_path} not found.")

    with file_path.open(encoding="utf-8") as f:
        data = json.load(f)

    data["status"] = decision
    data["reviewed_at"] = _now()
    data["reviewer_decision"] = decision
    if decision == "edited" and edited_reply is not None:
        data["edited_reply"] = edited_reply

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return data
