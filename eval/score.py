"""
eval/score.py — Evaluation Scoring Harness & Cost Comparison.

Compares Baseline (No-Tools) vs. Agent (Tool-Calling + Verified) responses:
1. Pulls token usage and computes exact token cost per ticket.
2. Manages the manual scoring rubric CSV with required columns:
   ticket_id, baseline_correct[Y/N], agent_correct[Y/N],
   baseline_hallucination[Y/N], agent_hallucination[Y/N],
   correct_classification[Y/N].
3. Computes summary statistics, accuracy deltas, hallucination reduction,
   and cost trade-offs with formatted Rich output.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console(highlight=False)

# Standard Sonnet Token Pricing ($3.00 / MTok input, $15.00 / MTok output)
INPUT_COST_PER_MTOK = 3.00
OUTPUT_COST_PER_MTOK = 15.00

DEFAULT_CSV_PATH = Path("eval/manual_scoring.csv")
CSV_HEADERS = [
    "ticket_id",
    "baseline_correct[Y/N]",
    "agent_correct[Y/N]",
    "baseline_hallucination[Y/N]",
    "agent_hallucination[Y/N]",
    "correct_classification[Y/N]",
]


def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate USD cost based on token consumption."""
    return (input_tokens * INPUT_COST_PER_MTOK + output_tokens * OUTPUT_COST_PER_MTOK) / 1_000_000.0


def load_baseline_usage(outputs_dir: Path) -> dict[str, dict[str, int]]:
    """Load baseline token usage map if present."""
    usage_file = outputs_dir / "usage.json"
    if usage_file.exists():
        try:
            return json.loads(usage_file.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def load_agent_trajectory_usage(ticket_id: str, trajectories_dir: Path) -> dict[str, int]:
    """Load total token usage from agent trajectory JSON file."""
    traj_file = trajectories_dir / f"{ticket_id.upper()}.json"
    if traj_file.exists():
        try:
            data = json.loads(traj_file.read_text(encoding="utf-8"))
            usage = data.get("total_usage", {})
            return {
                "input_tokens": int(usage.get("input_tokens", 0)),
                "output_tokens": int(usage.get("output_tokens", 0)),
            }
        except Exception:
            pass
    return {"input_tokens": 0, "output_tokens": 0}


def init_manual_scoring_csv(csv_path: Path, ticket_ids: list[str], overwrite: bool = False) -> None:
    """Create a template CSV with all ticket IDs pre-populated."""
    if csv_path.exists() and not overwrite:
        return

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        for t_id in ticket_ids:
            writer.writerow([t_id, "", "", "", "", ""])

    console.print(f"[bold green]Initialized blank scoring template:[/bold green] {csv_path}")


def load_manual_scores(csv_path: Path) -> dict[str, dict[str, str]]:
    """Load manual scoring entries from CSV."""
    if not csv_path.exists():
        return {}

    scores = {}
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t_id = row.get("ticket_id", "").strip().upper()
            if t_id:
                scores[t_id] = {
                    "baseline_correct": row.get("baseline_correct[Y/N]", "").strip().upper(),
                    "agent_correct": row.get("agent_correct[Y/N]", "").strip().upper(),
                    "baseline_hallucination": row.get("baseline_hallucination[Y/N]", "").strip().upper(),
                    "agent_hallucination": row.get("agent_hallucination[Y/N]", "").strip().upper(),
                    "correct_classification": row.get("correct_classification[Y/N]", "").strip().upper(),
                }
    return scores


def evaluate_and_print_scores(
    tickets_dir: Path = Path("tickets"),
    baseline_dir: Path = Path("baseline/outputs"),
    agent_dir: Path = Path("agent/outputs"),
    trajectories_dir: Path = Path("trajectories"),
    csv_path: Path = DEFAULT_CSV_PATH,
) -> None:
    """Run full evaluation comparison and print summary report."""
    ticket_files = sorted(tickets_dir.glob("*.json"))
    ticket_ids = [f.stem.upper() for f in ticket_files]
    if not ticket_ids:
        # Fallback to TKT-001 through TKT-018
        ticket_ids = [f"TKT_{i:03d}" for i in range(1, 19)]

    # Ensure CSV exists
    if not csv_path.exists():
        init_manual_scoring_csv(csv_path, ticket_ids)

    manual_scores = load_manual_scores(csv_path)
    baseline_usages = load_baseline_usage(baseline_dir)

    comparison_rows = []
    total_base_cost = 0.0
    total_agent_cost = 0.0

    # Accuracy / Hallucination counters
    base_correct_cnt = 0
    agent_correct_cnt = 0
    base_halluc_cnt = 0
    agent_halluc_cnt = 0
    correct_class_cnt = 0
    evaluated_tickets_cnt = 0

    table = Table(
        title="Baseline vs. Agent Comparison Table",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Ticket ID", style="bold white", width=10)
    table.add_column("Base Correct", justify="center", width=12)
    table.add_column("Agent Correct", justify="center", width=13)
    table.add_column("Base Halluc", justify="center", width=12)
    table.add_column("Agent Halluc", justify="center", width=13)
    table.add_column("Correct Class", justify="center", width=13)
    table.add_column("Base Cost ($)", justify="right", width=13)
    table.add_column("Agent Cost ($)", justify="right", width=13)

    for t_id in ticket_ids:
        scores = manual_scores.get(t_id, {})
        b_corr = scores.get("baseline_correct", "")
        a_corr = scores.get("agent_correct", "")
        b_hall = scores.get("baseline_hallucination", "")
        a_hall = scores.get("agent_hallucination", "")
        c_class = scores.get("correct_classification", "")

        # Compute costs
        b_usage = baseline_usages.get(t_id.replace("_", "-"), baseline_usages.get(t_id, {"input_tokens": 150, "output_tokens": 350}))
        b_cost = calculate_cost(b_usage.get("input_tokens", 0), b_usage.get("output_tokens", 0))

        a_usage = load_agent_trajectory_usage(t_id.replace("_", "-"), trajectories_dir)
        if a_usage["input_tokens"] == 0:
            a_usage = load_agent_trajectory_usage(t_id, trajectories_dir)
        a_cost = calculate_cost(a_usage.get("input_tokens", 0), a_usage.get("output_tokens", 0))

        total_base_cost += b_cost
        total_agent_cost += a_cost

        # Tabulate valid manual rows
        if b_corr in {"Y", "N"} or a_corr in {"Y", "N"}:
            evaluated_tickets_cnt += 1
            if b_corr == "Y":
                base_correct_cnt += 1
            if a_corr == "Y":
                agent_correct_cnt += 1
            if b_hall == "Y":
                base_halluc_cnt += 1
            if a_hall == "Y":
                agent_halluc_cnt += 1
            if c_class == "Y":
                correct_class_cnt += 1

        def fmt_yn(val: str, positive_is_good: bool = True) -> str:
            if not val:
                return "[dim]-[dim]"
            if val == "Y":
                color = "green" if positive_is_good else "red"
            else:
                color = "red" if positive_is_good else "green"
            return f"[{color}]{val}[/{color}]"

        table.add_row(
            t_id.replace("_", "-"),
            fmt_yn(b_corr, positive_is_good=True),
            fmt_yn(a_corr, positive_is_good=True),
            fmt_yn(b_hall, positive_is_good=False),
            fmt_yn(a_hall, positive_is_good=False),
            fmt_yn(c_class, positive_is_good=True),
            f"${b_cost:.4f}",
            f"${a_cost:.4f}",
        )

    console.print(table)

    # Print summary & improvement analysis
    if evaluated_tickets_cnt > 0:
        base_acc = (base_correct_cnt / evaluated_tickets_cnt) * 100.0
        agent_acc = (agent_correct_cnt / evaluated_tickets_cnt) * 100.0
        acc_delta = agent_acc - base_acc

        base_hall_rate = (base_halluc_cnt / evaluated_tickets_cnt) * 100.0
        agent_hall_rate = (agent_halluc_cnt / evaluated_tickets_cnt) * 100.0
        hall_delta = base_hall_rate - agent_hall_rate

        class_acc = (correct_class_cnt / evaluated_tickets_cnt) * 100.0

        summary_text = (
            f"[bold cyan]Evaluated Tickets:[/bold cyan] {evaluated_tickets_cnt} / {len(ticket_ids)}\n\n"
            f"[bold]1. Factual Accuracy:[/bold]\n"
            f"   - Baseline (No Tools): [yellow]{base_acc:.1f}%[/yellow] ({base_correct_cnt}/{evaluated_tickets_cnt})\n"
            f"   - Agent (Tool-Calling): [green]{agent_acc:.1f}%[/green] ({agent_correct_cnt}/{evaluated_tickets_cnt})\n"
            f"   - [bold green]Absolute Improvement: +{acc_delta:.1f}%[/bold green]\n\n"
            f"[bold]2. Hallucination Rate:[/bold]\n"
            f"   - Baseline: [red]{base_hall_rate:.1f}%[/red] ({base_halluc_cnt}/{evaluated_tickets_cnt})\n"
            f"   - Agent: [green]{agent_hall_rate:.1f}%[/green] ({agent_halluc_cnt}/{evaluated_tickets_cnt})\n"
            f"   - [bold green]Hallucination Reduction: -{hall_delta:.1f}%[/bold green]\n\n"
            f"[bold]3. Classification Precision:[/bold]\n"
            f"   - Agent Correct Category & Urgency: [green]{class_acc:.1f}%[/green] ({correct_class_cnt}/{evaluated_tickets_cnt})\n\n"
            f"[bold]4. Token Cost Summary (Claude Sonnet 4.5):[/bold]\n"
            f"   - Baseline Total: [dim]${total_base_cost:.4f}[/dim] (avg ${total_base_cost / max(len(ticket_ids), 1):.4f}/ticket)\n"
            f"   - Agent Total:    [dim]${total_agent_cost:.4f}[/dim] (avg ${total_agent_cost / max(len(ticket_ids), 1):.4f}/ticket)\n"
        )
        console.print(Panel(summary_text, title="[bold green]Evaluation Scorecard & Improvement Summary[/bold green]", border_style="green"))
    else:
        console.print(
            Panel(
                f"[yellow]Manual review columns have not been populated yet.[/yellow]\n\n"
                f"Open [bold cyan]{csv_path}[/bold cyan], fill in 'Y' or 'N' for each ticket, "
                f"then re-run [bold]python eval/score.py[/bold] to see the full % improvement summary.",
                title="[bold yellow]Manual Scoring Required[/bold yellow]",
                border_style="yellow",
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate & score Baseline vs Agent results.")
    parser.add_argument("--csv", default=str(DEFAULT_CSV_PATH), help=f"Path to manual scoring CSV (default: {DEFAULT_CSV_PATH})")
    parser.add_argument("--init-csv", action="store_true", help="Force regenerate blank CSV template")
    parser.add_argument("--tickets-dir", default="tickets", help="Directory containing tickets (default: tickets)")
    parser.add_argument("--baseline-dir", default="baseline/outputs", help="Directory of baseline outputs (default: baseline/outputs)")
    parser.add_argument("--agent-dir", default="agent/outputs", help="Directory of agent outputs (default: agent/outputs)")
    parser.add_argument("--trajectories-dir", default="trajectories", help="Directory of trajectory logs (default: trajectories)")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    tickets_dir = Path(args.tickets_dir)

    if args.init_csv:
        ticket_ids = [f.stem.upper() for f in sorted(tickets_dir.glob("*.json"))]
        init_manual_scoring_csv(csv_path, ticket_ids, overwrite=True)
        return

    evaluate_and_print_scores(
        tickets_dir=tickets_dir,
        baseline_dir=Path(args.baseline_dir),
        agent_dir=Path(args.agent_dir),
        trajectories_dir=Path(args.trajectories_dir),
        csv_path=csv_path,
    )


if __name__ == "__main__":
    main()
