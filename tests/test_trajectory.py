"""tests/test_trajectory.py — Unit tests for agent/trajectory.py"""

import json
from pathlib import Path

import pytest
from agent.trajectory import TrajectoryLogger


@pytest.fixture
def logger(tmp_path):
    return TrajectoryLogger(ticket_id="TEST-001", base_dir=str(tmp_path))


def _read(logger: TrajectoryLogger) -> dict:
    return json.loads(logger.path.read_text(encoding="utf-8"))


class TestTrajectoryLogger:
    def test_file_created_on_init(self, logger):
        assert logger.path.exists()

    def test_initial_structure(self, logger):
        data = _read(logger)
        assert data["ticket_id"] == "TEST-001"
        assert data["steps"] == []
        assert data["started_at"] is not None
        assert data["finished_at"] is None

    def test_log_tool_call(self, logger):
        logger.log_tool_call("classify_ticket", {"subject": "Hi", "body": "Help"})
        data = _read(logger)
        assert len(data["steps"]) == 1
        step = data["steps"][0]
        assert step["type"] == "tool_call"
        assert step["tool_name"] == "classify_ticket"
        assert step["tool_input"] == {"subject": "Hi", "body": "Help"}
        assert step["step"] == 1

    def test_log_tool_result(self, logger):
        logger.log_tool_result("classify_ticket", {"category": "billing"})
        data = _read(logger)
        step = data["steps"][0]
        assert step["type"] == "tool_result"
        assert step["tool_result"] == {"category": "billing"}

    def test_log_model_text(self, logger):
        logger.log_model_text("Here is my reasoning …")
        data = _read(logger)
        step = data["steps"][0]
        assert step["type"] == "model_text"
        assert step["text"] == "Here is my reasoning …"

    def test_step_counter_increments(self, logger):
        logger.log_tool_call("a", {})
        logger.log_tool_result("a", {})
        logger.log_model_text("text")
        data = _read(logger)
        assert [s["step"] for s in data["steps"]] == [1, 2, 3]

    def test_close_sets_finished_at(self, logger):
        path = logger.close()
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        assert data["finished_at"] is not None

    def test_close_returns_path_string(self, logger, tmp_path):
        path = logger.close()
        assert isinstance(path, str)
        assert Path(path).exists()

    def test_partial_run_is_readable(self, logger):
        """Even if close() is never called, the file should be valid JSON."""
        logger.log_tool_call("classify_ticket", {"subject": "x", "body": "y"})
        # Don't call close()
        data = _read(logger)
        assert len(data["steps"]) == 1
