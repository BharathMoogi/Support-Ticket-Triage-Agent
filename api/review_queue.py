"""
api/review_queue.py — Vercel serverless function for /api/review_queue
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from server import get_review_queue_data
import json


def handler(request, response):
    """Vercel Python handler interface."""
    data = get_review_queue_data()
    body = json.dumps(data).encode("utf-8")
    response.status_code = 200
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return body


def app(environ, start_response):
    """WSGI fallback."""
    body = json.dumps(get_review_queue_data()).encode("utf-8")
    start_response("200 OK", [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body)))
    ])
    return [body]


application = app
