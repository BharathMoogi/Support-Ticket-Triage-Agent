"""
api/eval.py — Vercel serverless function for /api/eval
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from server import get_eval_data
import json


def app(environ, start_response):
    """WSGI fallback."""
    body = json.dumps(get_eval_data()).encode("utf-8")
    start_response("200 OK", [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body)))
    ])
    return [body]


application = app
handler = app
