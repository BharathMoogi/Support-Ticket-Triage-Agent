"""
baseline/baseline.py — Zero-shot "no tools" baseline runner.

Iterates through all ticket JSON files in /tickets, sends only the subject and body
to the Anthropic API with a plain generic system prompt (no tools, no doc retrieval,
no customer context), and saves the generated replies into /baseline/outputs/{ticket_id}.txt.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import track
from rich.table import Table

load_dotenv()

console = Console()

SYSTEM_PROMPT = "You are a support agent. Write a helpful reply."
DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")


def load_tickets(tickets_dir: Path) -> list[dict]:
    """Load and sort all JSON ticket files from the target directory."""
    if not tickets_dir.exists():
        console.print(f"[red]Tickets directory not found:[/red] {tickets_dir}")
        sys.exit(1)

    tickets = []
    for filepath in sorted(tickets_dir.glob("*.json")):
        try:
            with filepath.open(encoding="utf-8") as f:
                data = json.load(f)
                data["_file_path"] = str(filepath)
                tickets.append(data)
        except Exception as exc:
            console.print(f"[yellow]Warning: Could not read {filepath.name}: {exc}[/yellow]")

    return tickets


def generate_baseline_reply(
    client: Any,
    subject: str,
    body: str,
    model: str = DEFAULT_MODEL,
    provider: str = "anthropic",
) -> tuple[str, int, int]:
    """Send only subject + body to LLM API with no tools or context."""
    user_content = f"Subject: {subject}\n\n{body}"

    if provider == "groq" or hasattr(client, "chat"):
        response = client.chat.completions.create(
            model=model,
            max_tokens=1500,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
        in_tokens = getattr(response.usage, "prompt_tokens", 0) if getattr(response, "usage", None) else 0
        out_tokens = getattr(response.usage, "completion_tokens", 0) if getattr(response, "usage", None) else 0
        reply_text = response.choices[0].message.content or ""
        return reply_text.strip(), in_tokens, out_tokens
    else:
        response = client.messages.create(
            model=model,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_content}
            ],
        )

        in_tokens = getattr(response.usage, "input_tokens", 0) if getattr(response, "usage", None) else 0
        out_tokens = getattr(response.usage, "output_tokens", 0) if getattr(response, "usage", None) else 0

        reply_text = ""
        for block in response.content:
            if getattr(block, "type", None) == "text":
                reply_text += block.text

        return reply_text.strip(), in_tokens, out_tokens


def run_baseline(
    tickets_dir: str = "tickets",
    outputs_dir: str = "baseline/outputs",
    model: str | None = None,
) -> int:
    """Execute baseline generation for all tickets in tickets_dir."""
    try:
        from agent.llm_adapter import get_llm_client
        provider, client, default_mod = get_llm_client()
        active_model = model or default_mod
    except Exception as e:
        console.print(f"[bold red]Error initializing LLM client:[/bold red] {e}")
        sys.exit(1)

    tickets_path = Path(tickets_dir)
    outputs_path = Path(outputs_dir)
    outputs_path.mkdir(parents=True, exist_ok=True)

    tickets = load_tickets(tickets_path)
    if not tickets:
        console.print(f"[yellow]No ticket JSON files found in {tickets_dir}[/yellow]")
        return 0

    console.print(
        f"[bold blue]Running No-Tools Baseline ({provider.upper()})[/bold blue] on [bold]{len(tickets)}[/bold] tickets "
        f"(Model: [cyan]{active_model}[/cyan])...\n"
    )

    generated_count = 0
    results_summary = []
    usage_map: dict[str, dict[str, int]] = {}

    import time
    for ticket in track(tickets, description="Generating baseline replies..."):
        ticket_id = str(ticket.get("id") or Path(ticket["_file_path"]).stem.upper()).replace("_", "-")
        subject = ticket.get("subject", "(No Subject)")
        body = ticket.get("body", "")

        try:
            reply, in_tok, out_tok = generate_baseline_reply(
                client, subject, body, model=active_model, provider=provider
            )
            output_file = outputs_path / f"{ticket_id}.txt"
            output_file.write_text(reply, encoding="utf-8")
            usage_map[ticket_id] = {"input_tokens": in_tok, "output_tokens": out_tok}

            generated_count += 1
            results_summary.append((ticket_id, subject, str(output_file), "Success"))
            time.sleep(0.5)  # rate limit spacing
        except Exception as exc:
            console.print(f"[red]Failed to generate reply for {ticket_id}: {exc}[/red]")
            results_summary.append((ticket_id, subject, "-", f"Error: {exc}"))

    # Save usage map to JSON
    (outputs_path / "usage.json").write_text(json.dumps(usage_map, indent=2), encoding="utf-8")

    # Summary table
    table = Table(title="Baseline Generation Summary", show_header=True, header_style="bold magenta")
    table.add_column("Ticket ID", style="cyan", width=12)
    table.add_column("Subject", style="white", max_width=45)
    table.add_column("Output File", style="dim", max_width=35)
    table.add_column("Status", style="green")

    for t_id, subj, out_p, status in results_summary:
        status_style = "green" if status == "Success" else "red"
        table.add_row(t_id, subj, out_p, f"[{status_style}]{status}[/{status_style}]")

    console.print(table)
    console.print(
        f"\n[bold green]Complete:[/bold green] Successfully generated [bold]{generated_count}/{len(tickets)}[/bold] "
        f"baseline replies in [cyan]{outputs_path}[/cyan]."
    )

    return generated_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate zero-shot no-tools baseline replies for support tickets.")
    parser.add_argument("--tickets-dir", default="tickets", help="Directory containing ticket JSON files (default: tickets)")
    parser.add_argument("--outputs-dir", default="baseline/outputs", help="Directory to save output TXT files (default: baseline/outputs)")
    parser.add_argument("--model", default=None, help="Model to use")
    args = parser.parse_args()

    run_baseline(
        tickets_dir=args.tickets_dir,
        outputs_dir=args.outputs_dir,
        model=args.model,
    )


if __name__ == "__main__":
    main()
