"""
eval/harness.py — Automated evaluation harness comparing Baseline vs. Triage Agent.
Executes test runs over /tickets and scores outputs against ground-truth labels.
"""

from __future__ import annotations
from typing import Any


def run_evaluation_suite(tickets_dir: str = "tickets", results_output_path: str = "eval/results.json") -> dict[str, Any]:
    """
    Run evaluation harness across all synthetic test tickets:
    - Runs baseline on each ticket
    - Runs agent on each ticket
    - Computes composite scores using eval/rubric.py
    - Outputs summary scorecard table
    """
    raise NotImplementedError("Eval harness execution will be implemented during eval phase.")


if __name__ == "__main__":
    print("Evaluation harness stub initialized.")
