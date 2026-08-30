"""
approve_reply.py — Human Approval & Review CLI.

Interactive CLI tool to inspect, approve, edit, or reject AI-generated
draft replies in /agent/review_queue/{ticket_id}.json.

Strict Safety Guarantee:
Nothing in this codebase calls any real send or email API. All decisions
are written back to the local review queue JSON files.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from agent.review_queue import (
    DEFAULT_QUEUE_DIR,
    list_review_queue,
    load_review_item,
    update_review_decision,
)

console = Console()


def show_queue_table(queue_dir: Path, status_filter: str | None = None) -> None:
    """Display tabular view of review queue items."""
    items = list_review_queue(queue_dir, status=status_filter)
    if not items:
        filter_str = f" with status '{status_filter}'" if status_filter else ""
        console.print(f"[yellow]No review items found in {queue_dir}{filter_str}.[/yellow]")
        return

    table = Table(
        title=f"Review Queue ({len(items)} items)",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Ticket ID", style="bold green", width=12)
    table.add_column("Customer", style="cyan", width=10)
    table.add_column("Subject", style="white", max_width=40)
    table.add_column("Status", style="bold")
    table.add_column("Queued At", style="dim", max_width=22)

    for item in items:
        status = item.get("status", "pending_review")
        if status == "approved":
            status_style = "green"
        elif status == "edited":
            status_style = "blue"
        elif status == "rejected":
            status_style = "red"
        else:
            status_style = "yellow"

        table.add_row(
            item.get("ticket_id", "-"),
            item.get("customer_id", "-"),
            item.get("subject", "-"),
            f"[{status_style}]{status}[/{status_style}]",
            item.get("queued_at", "-")[:19],
        )

    console.print(table)


def review_single_item(item: dict, queue_dir: Path) -> str:
    """Prompt reviewer to approve, edit, reject, or skip a single item."""
    t_id = item.get("ticket_id", "UNKNOWN")
    c_id = item.get("customer_id", "UNKNOWN")
    subject = item.get("subject", "(No Subject)")
    draft = item.get("draft_reply", "(No Draft)")
    v_info = item.get("verification_info", {})
    v_status = v_info.get("status", "unverified")

    header_info = (
        f"[bold cyan]Ticket ID:[/bold cyan] {t_id}  |  "
        f"[bold cyan]Customer:[/bold cyan] {c_id}  |  "
        f"[bold cyan]Verification:[/bold cyan] [green]{v_status}[/green]\n"
        f"[bold cyan]Subject:[/bold cyan] {subject}"
    )

    console.print("\n" + "=" * 70)
    console.print(Panel(header_info, border_style="cyan"))
    console.print(Panel(draft, title="[bold green]Draft Reply to Customer[/bold green]", border_style="green"))

    choice = Prompt.ask(
        "\nAction: [[bold green]A[/bold green]]pprove / [[bold blue]E[/bold blue]]dit / [[bold red]R[/bold red]]eject / [[bold yellow]S[/bold yellow]]kip / [[bold white]Q[/bold white]]uit",
        choices=["a", "e", "r", "s", "q", "A", "E", "R", "S", "Q"],
        default="a",
    ).lower()

    if choice == "a":
        update_review_decision(t_id, decision="approved", queue_dir=queue_dir)
        console.print(f"[bold green]✓ Approved {t_id}. Marked as approved in review queue.[/bold green]")
    elif choice == "e":
        console.print("[dim]Enter the revised reply text below (press Enter, then type EOF or press Ctrl+D/Z on empty line to finish):[/dim]")
        lines = []
        try:
            while True:
                line = input()
                if line.strip() == "EOF":
                    break
                lines.append(line)
        except EOFError:
            pass

        edited_text = "\n".join(lines).strip()
        if not edited_text:
            edited_text = draft

        update_review_decision(t_id, decision="edited", edited_reply=edited_text, queue_dir=queue_dir)
        console.print(f"[bold blue]✓ Saved edited draft for {t_id} and marked as edited.[/bold blue]")
    elif choice == "r":
        update_review_decision(t_id, decision="rejected", queue_dir=queue_dir)
        console.print(f"[bold red]✗ Rejected {t_id}. Marked as rejected in review queue.[/bold red]")
    elif choice == "s":
        console.print(f"[yellow]Skipped {t_id}. Remains in pending_review.[/yellow]")
    elif choice == "q":
        return "quit"

    return "continue"


def main() -> None:
    parser = argparse.ArgumentParser(description="Human Approval and Review CLI for Support Drafts.")
    parser.add_argument("--queue-dir", default=str(DEFAULT_QUEUE_DIR), help="Directory of review queue files (default: agent/review_queue)")
    parser.add_argument("--list", action="store_true", help="List all review queue items")
    parser.add_argument("--status", default=None, help="Filter list by status (e.g. pending_review, approved, edited, rejected)")
    parser.add_argument("--ticket", default=None, help="Review a specific ticket ID (e.g. TKT-001)")
    args = parser.parse_args()

    queue_dir = Path(args.queue_dir)

    if args.list:
        show_queue_table(queue_dir, status_filter=args.status)
        return

    if args.ticket:
        item = load_review_item(args.ticket, queue_dir=queue_dir)
        if not item:
            console.print(f"[red]Ticket {args.ticket} not found in {queue_dir}[/red]")
            sys.exit(1)
        review_single_item(item, queue_dir=queue_dir)
        return

    # Interactive review mode over pending items
    pending_items = list_review_queue(queue_dir, status="pending_review")
    if not pending_items:
        console.print(f"[bold green]No pending items in {queue_dir}![/bold green]")
        show_queue_table(queue_dir)
        return

    console.print(f"[bold cyan]Found {len(pending_items)} pending drafts for review.[/bold cyan]")
    for item in pending_items:
        res = review_single_item(item, queue_dir=queue_dir)
        if res == "quit":
            console.print("\n[yellow]Review session ended.[/yellow]")
            break

    console.print("\n[bold]Current Review Queue Status:[/bold]")
    show_queue_table(queue_dir)


if __name__ == "__main__":
    main()
