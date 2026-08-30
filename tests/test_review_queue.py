"""tests/test_review_queue.py — Unit tests for agent/review_queue.py"""

import json
from pathlib import Path

import pytest
from agent.review_queue import (
    write_to_review_queue,
    list_review_queue,
    load_review_item,
    update_review_decision,
)


@pytest.fixture
def queue_dir(tmp_path) -> Path:
    q_dir = tmp_path / "review_queue"
    q_dir.mkdir(parents=True, exist_ok=True)
    return q_dir


def test_write_to_review_queue_creates_file(queue_dir):
    path = write_to_review_queue(
        ticket_id="TKT-001",
        customer_id="CUST-101",
        subject="Export CSV",
        draft_reply="Here is how to export...",
        verification_info={"status": "passed_first_pass"},
        trajectory_path="trajectories/TKT-001.json",
        queue_dir=queue_dir,
    )
    assert path.exists()
    assert path.name == "TKT-001.json"

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["ticket_id"] == "TKT-001"
    assert data["customer_id"] == "CUST-101"
    assert data["status"] == "pending_review"
    assert data["draft_reply"] == "Here is how to export..."
    assert data["reviewer_decision"] is None


def test_list_review_queue(queue_dir):
    for i in range(1, 4):
        write_to_review_queue(
            ticket_id=f"TKT-{i:03d}",
            customer_id=f"CUST-{i:03d}",
            subject=f"Subject {i}",
            draft_reply=f"Draft {i}",
            queue_dir=queue_dir,
        )

    items = list_review_queue(queue_dir)
    assert len(items) == 3
    assert [item["ticket_id"] for item in items] == ["TKT-001", "TKT-002", "TKT-003"]


def test_load_review_item(queue_dir):
    write_to_review_queue(
        ticket_id="TKT-042",
        customer_id="CUST-042",
        subject="Special case",
        draft_reply="Draft reply content",
        queue_dir=queue_dir,
    )
    item = load_review_item("TKT-042", queue_dir=queue_dir)
    assert item is not None
    assert item["ticket_id"] == "TKT-042"

    missing = load_review_item("TKT-999", queue_dir=queue_dir)
    assert missing is None


def test_update_review_decision_approved(queue_dir):
    write_to_review_queue(
        ticket_id="TKT-010",
        customer_id="CUST-110",
        subject="Sync bug",
        draft_reply="Bug fix steps",
        queue_dir=queue_dir,
    )
    updated = update_review_decision("TKT-010", decision="approved", queue_dir=queue_dir)
    assert updated["status"] == "approved"
    assert updated["reviewer_decision"] == "approved"
    assert updated["reviewed_at"] is not None


def test_update_review_decision_edited(queue_dir):
    write_to_review_queue(
        ticket_id="TKT-011",
        customer_id="CUST-111",
        subject="Quota bug",
        draft_reply="Original draft",
        queue_dir=queue_dir,
    )
    updated = update_review_decision(
        "TKT-011",
        decision="edited",
        edited_reply="Custom revised human text",
        queue_dir=queue_dir,
    )
    assert updated["status"] == "edited"
    assert updated["edited_reply"] == "Custom revised human text"
