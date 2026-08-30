"""
api/decide.py — Vercel serverless function for POST /api/decide
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import json
from server import BASE_DIR


def app(environ, start_response):
    """WSGI handler for POST /api/decide."""
    try:
        content_length = int(environ.get("CONTENT_LENGTH", 0))
        body_bytes = environ["wsgi.input"].read(content_length)
        payload = json.loads(body_bytes.decode("utf-8"))
        t_id = payload.get("ticket_id")
        decision = payload.get("decision")
        edited_reply = payload.get("edited_reply")

        if t_id and decision:
            try:
                from agent.review_queue import update_review_decision
                update_review_decision(
                    t_id,
                    decision=decision,
                    edited_reply=edited_reply,
                    queue_dir=BASE_DIR / "agent" / "review_queue",
                )
            except Exception:
                pass

        resp = json.dumps({"status": "ok"}).encode("utf-8")
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


application = app
handler = app
