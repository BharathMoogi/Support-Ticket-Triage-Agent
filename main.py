"""
main.py — CLI entry point for the Ticket Triage Agent.

Usage:
    # Triage a specific ticket from the sample data file by ID
    python main.py --id TKT-001

    # Triage all tickets in the sample data file
    python main.py --all

    # Triage a ticket supplied as inline JSON
    python main.py --json '{"id":"TKT-099","subject":"Help!","body":"My account is broken."}'

    # Use a different data file
    python main.py --id TKT-001 --data path/to/tickets.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()

console = Console()


def _load_ticket_by_id(data_file: str, ticket_id: str) -> dict:
    path = Path(data_file)
    if not path.exists():
        console.print(f"[red]Data file not found:[/red] {data_file}")
        sys.exit(1)
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            ticket = json.loads(line)
            if ticket.get("id") == ticket_id:
                return ticket
    console.print(f"[red]Ticket {ticket_id!r} not found in {data_file}[/red]")
    sys.exit(1)


def _load_all_tickets(data_file: str) -> list[dict]:
    path = Path(data_file)
    if not path.exists():
        console.print(f"[red]Data file not found:[/red] {data_file}")
        sys.exit(1)
    tickets = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                tickets.append(json.loads(line))
    return tickets


def _print_result(result: dict) -> None:
    """Pretty-print the triage result to the console."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_row("[bold cyan]Ticket ID[/bold cyan]", result["ticket_id"])
    table.add_row("[bold cyan]Trajectory[/bold cyan]", result["trajectory_path"])
    table.add_row("[bold cyan]Review Queue[/bold cyan]", result["queue_path"])
    console.print(table)
    console.print(
        Panel(
            result["draft_reply"],
            title="[bold green]Draft Reply (pending human review)[/bold green]",
            border_style="green",
        )
    )


def _run_one(ticket: dict) -> None:
    from agent.run import run_triage  # import here so env is loaded first

    console.rule(f"[bold]Triaging {ticket.get('id', '?')}[/bold]")
    with console.status(f"Running agent for {ticket.get('id')} …"):
        result = run_triage(ticket)
    _print_result(result)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ticket Triage Agent — powered by Claude"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", metavar="TICKET_ID", help="Triage a single ticket by ID")
    group.add_argument("--all", action="store_true", help="Triage all tickets in the data file")
    group.add_argument(
        "--json",
        metavar="JSON_STRING",
        help="Triage a ticket supplied as an inline JSON string",
    )
    parser.add_argument(
        "--data",
        default="data/tickets.jsonl",
        metavar="FILE",
        help="Path to JSONL ticket data file (default: data/tickets.jsonl)",
    )
    args = parser.parse_args()

    if args.json:
        try:
            ticket = json.loads(args.json)
        except json.JSONDecodeError as exc:
            console.print(f"[red]Invalid JSON:[/red] {exc}")
            sys.exit(1)
        _run_one(ticket)

    elif args.id:
        ticket = _load_ticket_by_id(args.data, args.id)
        _run_one(ticket)

    elif args.all:
        tickets = _load_all_tickets(args.data)
        console.print(f"[bold]Found {len(tickets)} ticket(s) to triage.[/bold]")
        for ticket in tickets:
            _run_one(ticket)
            console.print()

    console.print("\n[bold green]Done.[/bold green] Check review_queue/pending.jsonl for drafts awaiting approval.")


if __name__ == "__main__":
    main()
