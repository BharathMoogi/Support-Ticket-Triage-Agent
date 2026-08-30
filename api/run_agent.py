"""
api/run_agent.py — Vercel serverless function for POST /api/run_agent
"""
from __future__ import annotations

import json
import os
import sys
import traceback
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

        # Locate ticket file — filenames use underscores (tkt_001.json), IDs use hyphens (TKT-001)
        tickets_dir = root_dir / "tickets"
        ticket_file = None
        # Normalise: TKT-001 → tkt_001
        normalised = ticket_id.lower().replace("-", "_")
        for candidate in [
            tickets_dir / f"{normalised}.json",
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

        # Vercel /var/task/ is read-only — write trajectories and queue to /tmp/
        import tempfile
        is_vercel = os.getenv("VERCEL") or os.getenv("VERCEL_ENV") or os.getenv("VERCEL_REGION")
        if is_vercel:
            tmp_base = Path("/tmp")
        else:
            tmp_base = root_dir

        traj_dir = str(tmp_base / "trajectories")
        queue_dir = str(tmp_base / "agent" / "review_queue")
        Path(traj_dir).mkdir(parents=True, exist_ok=True)
        Path(queue_dir).mkdir(parents=True, exist_ok=True)

        # Run full triage pipeline (Groq or Anthropic auto-selected via env vars)
        draft, traj_path, queue_path = run_ticket_agent(
            ticket=ticket_data,
            trajectories_dir=traj_dir,
            queue_dir=queue_dir,
        )

        # Read back queue file for category/urgency/verification metadata
        queue_json_path = Path(queue_dir) / f"{ticket_id.upper()}.json"
        queue_data = {}
        if queue_json_path.exists():
            with queue_json_path.open(encoding="utf-8") as f:
                queue_data = json.load(f)

        resp = json.dumps({
            "status": "ok",
            "ticket_id": ticket_id,
            "draft_reply": draft,
            "category": queue_data.get("category"),
            "urgency": queue_data.get("urgency"),
            "verification": queue_data.get("verification_info", {}).get("verification"),
        }).encode("utf-8")

        start_response("200 OK", [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(resp)))
        ])
        return [resp]

    except Exception as e:
        tb = traceback.format_exc()
        err = json.dumps({"error": str(e), "traceback": tb}).encode("utf-8")
        start_response("400 Bad Request", [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(err)))
        ])
        return [err]


handler = app
application = app
