"""tests/test_score.py — Unit tests for eval/score.py"""

import csv
from pathlib import Path
import pytest
from eval.score import (
    calculate_cost,
    init_manual_scoring_csv,
    load_manual_scores,
    CSV_HEADERS,
)


def test_calculate_cost_standard_pricing():
    # 1,000 input tokens ($0.003) + 1,000 output tokens ($0.015) = $0.018
    cost = calculate_cost(1000, 1000)
    assert round(cost, 5) == 0.018


def test_init_manual_scoring_csv(tmp_path):
    csv_file = tmp_path / "test_scoring.csv"
    ticket_ids = ["TKT-001", "TKT-002"]
    init_manual_scoring_csv(csv_file, ticket_ids)
    assert csv_file.exists()

    with csv_file.open(encoding="utf-8") as f:
        reader = list(csv.reader(f))
        assert reader[0] == CSV_HEADERS
        assert len(reader) == 3


def test_load_manual_scores(tmp_path):
    csv_file = tmp_path / "test_scoring.csv"
    with csv_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        writer.writerow(["TKT-001", "N", "Y", "Y", "N", "Y"])

    scores = load_manual_scores(csv_file)
    assert "TKT-001" in scores
    assert scores["TKT-001"]["baseline_correct"] == "N"
    assert scores["TKT-001"]["agent_correct"] == "Y"
    assert scores["TKT-001"]["baseline_hallucination"] == "Y"
    assert scores["TKT-001"]["agent_hallucination"] == "N"
    assert scores["TKT-001"]["correct_classification"] == "Y"
