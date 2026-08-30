"""
api/run_agent.py — Vercel serverless function for POST /api/run_agent
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from agent.main import run_ticket_agent


def app(environ, start_response):
    """WSGI handler for POST /api/run_agent."""
    method = environ.get("REQUEST_METHOD", "GET").upper()
    if method != "POST":
        not_allowed = b'{"error": "Method Not Allowed"}'
        start_response("405 Method Not Allowed", [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(not_allowed)))
        ])
        return [not_allowed]

    try:
        content_length = int(environ.get("CONTENT_LENGTH", 0))
        body_bytes = environ["wsgi.input"].read(content_length) if content_length > 0 else b"{}"
        payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        ticket_id = payload.get("ticket_id")

        if not ticket_id:
            raise ValueError("ticket_id is required (e.g. {'ticket_id': 'TKT-001'})")

        # Locate ticket file
        tickets_dir = root_dir / "tickets"
        ticket_file = None
        for candidate in [
            tickets_dir / f"{ticket_id.lower()}.json",
            tickets_dir / f"{ticket_id}.json",
            tickets_dir / f"{ticket_id.upper()}.json",
        ]:
            if candidate.exists():
                ticket_file = candidate
                break

        if not ticket_file:
            raise FileNotFoundError(f"Ticket {ticket_id} not found in tickets directory.")

        with ticket_file.open(encoding="utf-8") as f:
            ticket_data = json.load(f)

        # Run full triage pipeline (Groq or Anthropic auto-selected via .env)
        draft, traj_path, queue_path = run_ticket_agent(
            ticket=ticket_data,
            trajectories_dir=str(root_dir / "trajectories"),
            queue_dir=str(root_dir / "agent" / "review_queue"),
        )

        resp = json.dumps({
            "status": "ok",
            "ticket_id": ticket_id,
            "draft_reply": draft,
            "trajectory_path": traj_path,
            "queue_path": queue_path,
        }).encode("utf-8")

        start_response("200 OK", [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(resp)))
        ])
        return [resp]

    except Exception as e:
        err = json.dumps({"error": str(e)}).encode("utf-8")
        start_response("400 Bad Request", [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(err)))
        ])
        return [err]


handler = app
application = app
