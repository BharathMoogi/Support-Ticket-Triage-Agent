"""
agent/trajectory.py — Per-ticket JSON trajectory logger.

Creates trajectories/<ticket_id>.json and records every step of the
agentic loop: tool calls, results, and Claude's reasoning text.

File format:
{
  "ticket_id": "TKT-001",
  "started_at": "<ISO8601>",
  "finished_at": "<ISO8601>",   # added on close()
  "steps": [
    {
      "step": 1,
      "type": "tool_call" | "tool_result" | "model_text",
      "timestamp": "<ISO8601>",
      "tool_name": "...",       # for tool_call / tool_result
      "tool_input": {...},      # for tool_call
      "tool_result": {...},     # for tool_result
      "text": "..."             # for model_text
    },
    ...
  ]
}
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TrajectoryLogger:
    """
    Manages the trajectory JSON file for a single agent run.

    Usage:
        logger = TrajectoryLogger(ticket_id="TKT-001")
        logger.log_tool_call(tool_name, tool_input)
        logger.log_tool_result(tool_name, result)
        logger.log_model_text(text)
        logger.close()
    """

    def __init__(self, ticket_id: str, base_dir: str | None = None) -> None:
        base_dir = base_dir or os.getenv("TRAJECTORIES_DIR", "trajectories")
        Path(base_dir).mkdir(parents=True, exist_ok=True)
        self.path = Path(base_dir) / f"{ticket_id}.json"
        self._data: dict = {
            "ticket_id": ticket_id,
            "started_at": _now(),
            "finished_at": None,
            "total_usage": {"input_tokens": 0, "output_tokens": 0},
            "steps": [],
        }
        self._step = 0
        self._flush()  # create the file immediately so it exists after __init__

    def _append(self, record: dict) -> None:
        self._step += 1
        record["step"] = self._step
        record["timestamp"] = _now()
        self._data["steps"].append(record)
        self._flush()

    def _flush(self) -> None:
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_tool_call(self, tool_name: str, tool_input: dict) -> None:
        """Record a tool invocation by Claude."""
        self._append(
            {"type": "tool_call", "tool_name": tool_name, "tool_input": tool_input}
        )

    def log_tool_result(self, tool_name: str, result: object) -> None:
        """Record the Python result returned to Claude."""
        self._append(
            {"type": "tool_result", "tool_name": tool_name, "tool_result": result}
        )

    def log_model_text(self, text: str) -> None:
        """Record a text block emitted by Claude (reasoning or final reply)."""
        self._append({"type": "model_text", "text": text})

    def log_verification(self, verification_data: dict) -> None:
        """Record draft verification & groundedness check results."""
        self._append({"type": "verification", "data": verification_data})

    def log_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Accumulate token usage for the run."""
        self._data["total_usage"]["input_tokens"] += int(input_tokens or 0)
        self._data["total_usage"]["output_tokens"] += int(output_tokens or 0)
        self._flush()

    def close(self) -> str:
        """Mark the trajectory complete and return the file path."""
        self._data["finished_at"] = _now()
        self._flush()
        return str(self.path)
