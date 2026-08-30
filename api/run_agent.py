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

import anthropic
from agent.main import process_ticket


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

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is not configured. "
                "Please add ANTHROPIC_API_KEY in Vercel Settings -> Environment Variables, then redeploy."
            )

        client = anthropic.Anthropic(api_key=api_key)
        tickets_dir = root_dir / "tickets"

        if not ticket_id:
            raise ValueError("ticket_id is required in request payload (e.g. {'ticket_id': 'TICK-001'})")

        # Locate ticket file
        candidate_files = [
            tickets_dir / f"{ticket_id.lower()}.json",
            tickets_dir / f"{ticket_id}.json",
            tickets_dir / f"{ticket_id.upper()}.json",
        ]
        ticket_file = None
        for f in candidate_files:
            if f.exists():
                ticket_file = f
                break

        if not ticket_file:
            raise FileNotFoundError(f"Ticket {ticket_id} not found in tickets directory.")

        # Execute full triage pipeline with tool calls + verification
        traj = process_ticket(ticket_file, client=client)

        resp = json.dumps({
            "status": "ok",
            "ticket_id": ticket_id,
            "category": traj.get("category"),
            "urgency": traj.get("urgency"),
            "verification": traj.get("verification"),
            "draft_reply": traj.get("draft_reply"),
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
