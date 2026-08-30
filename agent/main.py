"""
agent/main.py — Full Tool-Calling Support Triage Agent Loop.

Orchestrates the Anthropic Claude agentic loop over FlowBoard support tickets:
- Registers search_docs, get_customer_context, and classify_ticket as tools.
- Strictly logs all tool calls, inputs, outputs, and model reasoning into /trajectories/{ticket_id}.json.
- Iterates over all tickets in /tickets and writes final drafts to /agent/outputs/{ticket_id}.txt.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import track
from rich.table import Table

# Ensure project root is on sys.path for direct execution
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from agent.classify import classify_ticket
from agent.customer_context import get_customer_context
from agent.retrieval import search_docs
from agent.review_queue import write_to_review_queue
from agent.trajectory import TrajectoryLogger
from agent.verify import verify_and_refine_draft

load_dotenv()

console = Console()

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
MAX_ITERATIONS = 12

# ---------------------------------------------------------------------------
# Tool Schemas for Anthropic Tool Use
# ---------------------------------------------------------------------------

AGENT_TOOLS = [
    {
        "name": "classify_ticket",
        "description": "Classify ticket into category ('billing', 'bug', 'how-to', 'other') and urgency ('low', 'medium', 'high').",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticket_text": {"type": "string", "description": "The ticket subject and body text to evaluate."},
            },
            "required": ["ticket_text"],
        },
    },
    {
        "name": "search_docs",
        "description": "Search FlowBoard help-center articles for troubleshooting steps, policy rules, or feature guides.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search terms, error messages, or feature keywords."},
                "k": {"type": "integer", "description": "Number of documentation chunks to retrieve (default: 3).", "default": 3},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_customer_context",
        "description": "Look up account metadata (plan, signup date, past ticket count) for a specific customer ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "The customer identifier (e.g. 'CUST-101')."},
            },
            "required": ["customer_id"],
        },
    },
]

SYSTEM_PROMPT = """\
You are FlowBoard's expert support-ticket triage agent.
Your mission is to analyze incoming customer support tickets, gather required context using tools, and compose an accurate, professional, and empathetic draft reply.

Strict Operational Guidelines:
1. Always call `classify_ticket` first to establish the category and urgency level.
2. Call `search_docs` for any factual, policy (refunds, pricing, cancellations), or technical troubleshooting questions. Ground your reply directly on the retrieved documentation.
3. Call `get_customer_context` when the ticket involves account-specific information, plan limits, billing history, or tier permissions (e.g. Free vs Pro vs Team).
4. If a ticket requests impossible, contradictory, or non-existent features (e.g. 3D holographic VR or quantum links), politely clarify that FlowBoard does not support this and explain actual supported capabilities.
5. If a ticket is emotionally charged or urgent, acknowledge their frustration with empathy and outline concrete immediate next steps.
6. When all context is gathered, write a clear, complete, and grounded final draft response.
"""
GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["input_schema"],
        },
    }
    for t in AGENT_TOOLS
]


def _dispatch_tool(tool_name: str, tool_input: dict[str, Any], client: Any = None) -> Any:
    """Execute a local tool function by name."""
    if tool_name == "classify_ticket":
        text = tool_input.get("ticket_text", "")
        return classify_ticket(text, client=client)
    elif tool_name == "search_docs":
        query = tool_input.get("query", "")
        k = int(tool_input.get("k", 3))
        # Always use absolute path for docs/ — never trust relative CWD or "." values.
        # DOCS_DIR env var is only used if it resolves to a real, non-root directory.
        _env_docs = os.getenv("DOCS_DIR", "").strip()
        _abs_project_docs = _PROJECT_ROOT / "docs"
        if _env_docs and _env_docs not in (".", "./", "/"):
            _candidate = Path(_env_docs)
            docs_dir = str(_candidate) if _candidate.is_dir() else str(_abs_project_docs)
        else:
            docs_dir = str(_abs_project_docs)
        return search_docs(query, k=k, docs_dir=docs_dir)
    elif tool_name == "get_customer_context":
        cid = tool_input.get("customer_id", "")
        ctx = get_customer_context(cid)
        return ctx if ctx is not None else {"error": f"Customer ID '{cid}' not found in database."}
    else:
        return {"error": f"Unknown tool '{tool_name}'"}


def run_ticket_agent(
    ticket: dict[str, Any],
    client: Any = None,
    model: str | None = None,
    trajectories_dir: str = "trajectories",
    queue_dir: str = "agent/review_queue",
) -> tuple[str, str, str]:
    """
    Run full tool-calling agent loop on a single ticket (supports Groq & Anthropic).
    """
    ticket_id = str(ticket.get("id") or "UNKNOWN").upper()
    customer_id = ticket.get("customer_id", "UNKNOWN")
    subject = ticket.get("subject", "(No Subject)")
    body = ticket.get("body", "")

    logger = TrajectoryLogger(ticket_id=ticket_id, base_dir=trajectories_dir)

    user_message = (
        f"Ticket ID: {ticket_id}\n"
        f"Customer ID: {customer_id}\n"
        f"Subject: {subject}\n\n"
        f"Body:\n{body}"
    )

    draft_reply = ""
    retrieved_chunks: list[dict[str, Any]] = []
    customer_context: dict[str, Any] | None = None
    iteration = 0

    groq_key = os.getenv("GROQ_API_KEY")
    is_groq = bool(groq_key and (client is None or hasattr(client, "chat")))

    if is_groq:
        from groq import Groq
        if client is None:
            from agent.llm_adapter import _make_groq_client
            client = _make_groq_client(groq_key)
        groq_model = model or os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        while iteration < MAX_ITERATIONS:
            iteration += 1
            response = client.chat.completions.create(
                model=groq_model,
                messages=messages,
                tools=GROQ_TOOLS,
                tool_choice="auto",
                temperature=0.1,
            )

            if getattr(response, "usage", None):
                logger.log_usage(response.usage.prompt_tokens, response.usage.completion_tokens)

            choice = response.choices[0]
            msg = choice.message
            content = msg.content or ""

            if content.strip():
                logger.log_model_text(content)
                if len(content.strip()) > 30:
                    draft_reply = content.strip()

            if not msg.tool_calls:
                break

            messages.append(msg)

            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_input = json.loads(tool_call.function.arguments)
                except Exception:
                    tool_input = {}

                logger.log_tool_call(tool_name, tool_input)
                result = _dispatch_tool(tool_name, tool_input, client=client)
                logger.log_tool_result(tool_name, result)

                if tool_name == "search_docs" and isinstance(result, list):
                    retrieved_chunks.extend(result)
                elif tool_name == "get_customer_context" and isinstance(result, dict) and "error" not in result:
                    customer_context = result

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(result, ensure_ascii=False),
                })

    else:
        if client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("No API key configured.")
            client = anthropic.Anthropic(api_key=api_key)
        anthropic_model = model or DEFAULT_MODEL

        messages = [
            {"role": "user", "content": user_message}
        ]

        while iteration < MAX_ITERATIONS:
            iteration += 1
            response = client.messages.create(
                model=anthropic_model,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=AGENT_TOOLS,
                messages=messages,
            )

            if getattr(response, "usage", None):
                logger.log_usage(response.usage.input_tokens, response.usage.output_tokens)

            for block in response.content:
                if getattr(block, "type", None) == "text" and block.text.strip():
                    logger.log_model_text(block.text)
                    if len(block.text.strip()) > 30:
                        draft_reply = block.text.strip()

            if response.stop_reason == "end_turn":
                break

            tool_use_blocks = [b for b in response.content if getattr(b, "type", None) == "tool_use"]
            if not tool_use_blocks:
                break

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in tool_use_blocks:
                tool_name = block.name
                tool_input = block.input

                logger.log_tool_call(tool_name, tool_input)
                result = _dispatch_tool(tool_name, tool_input, client=client)
                logger.log_tool_result(tool_name, result)

                if tool_name == "search_docs" and isinstance(result, list):
                    retrieved_chunks.extend(result)
                elif tool_name == "get_customer_context" and isinstance(result, dict) and "error" not in result:
                    customer_context = result

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

            messages.append({"role": "user", "content": tool_results})

    # Post-generation factual verification & refinement
    final_draft, verification_log = verify_and_refine_draft(
        draft_reply=draft_reply,
        retrieved_chunks=retrieved_chunks,
        customer_context=customer_context,
        client=client,
        model=model,
    )
    logger.log_verification(verification_log)

    trajectory_path = logger.close()

    # Write to human review queue (no real send API is ever called)
    review_path = write_to_review_queue(
        ticket_id=ticket_id,
        customer_id=customer_id,
        subject=subject,
        draft_reply=final_draft,
        verification_info=verification_log,
        trajectory_path=trajectory_path,
        queue_dir=queue_dir,
    )

    return final_draft, trajectory_path, str(review_path)


def run_all_tickets(
    tickets_dir: str = "tickets",
    outputs_dir: str = "agent/outputs",
    trajectories_dir: str = "trajectories",
    queue_dir: str = "agent/review_queue",
    model: str | None = None,
    single_id: str | None = None,
) -> int:
    """Run agent loop across ticket dataset using available provider (Groq or Anthropic)."""
    groq_key = os.getenv("GROQ_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if groq_key:
        from agent.llm_adapter import _make_groq_client
        client = _make_groq_client(groq_key)
        active_model = model or os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
        provider_name = "Groq (Free Cloud Inference)"
    elif anthropic_key:
        client = anthropic.Anthropic(api_key=anthropic_key)
        active_model = model or DEFAULT_MODEL
        provider_name = "Anthropic Claude"
    else:
        console.print("[bold red]Error:[/bold red] No API key found. Set GROQ_API_KEY or ANTHROPIC_API_KEY.")
        sys.exit(1)

    tickets_path = Path(tickets_dir)
    outputs_path = Path(outputs_dir)
    outputs_path.mkdir(parents=True, exist_ok=True)

    ticket_files = sorted(tickets_path.glob("*.json"))
    if single_id:
        ticket_files = [f for f in ticket_files if single_id.lower() in f.stem.lower()]

    if not ticket_files:
        console.print(f"[yellow]No tickets found in {tickets_dir}[/yellow]")
        return 0

    console.print(
        f"[bold blue]Starting FlowBoard Agent Loop[/bold blue] on [bold]{len(ticket_files)}[/bold] tickets "
        f"(Provider: [green]{provider_name}[/green], Model: [cyan]{active_model}[/cyan])...\n"
    )

    success_count = 0
    summary_rows = []

    import time

    for tf in track(ticket_files, description="Processing tickets with Agent tools..."):
        try:
            with tf.open(encoding="utf-8") as f:
                ticket_data = json.load(f)

            t_id = ticket_data.get("id", tf.stem.upper())
            draft, traj_path, q_path = run_ticket_agent(
                ticket=ticket_data,
                client=client,
                model=active_model,
                trajectories_dir=trajectories_dir,
                queue_dir=queue_dir,
            )

            out_file = outputs_path / f"{t_id}.txt"
            out_file.write_text(draft, encoding="utf-8")

            success_count += 1
            summary_rows.append((t_id, ticket_data.get("subject", ""), str(out_file), q_path, "Success"))
            time.sleep(0.5)
        except Exception as exc:
            console.print(f"[red]Error on {tf.name}: {exc}[/red]")
            summary_rows.append((tf.stem.upper(), "-", "-", "-", f"Failed: {exc}"))

    # Render summary table
    table = Table(title="Agent Execution Summary", show_header=True, header_style="bold cyan")
    table.add_column("Ticket ID", style="bold green", width=10)
    table.add_column("Subject", style="white", max_width=35)
    table.add_column("Draft Output", style="dim", max_width=25)
    table.add_column("Review Queue File", style="dim", max_width=28)
    table.add_column("Status", style="bold")

    for t_id, subj, out_p, q_p, status in summary_rows:
        color = "green" if "Success" in status else "red"
        table.add_row(t_id, subj, out_p, q_p, f"[{color}]{status}[/{color}]")

    console.print(table)
    console.print(
        f"\n[bold green]Complete:[/bold green] Successfully processed {success_count}/{len(ticket_files)} tickets.\n"
        f"[cyan]Review drafts with:[/cyan] [bold]python approve_reply.py[/bold]"
    )
    return success_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the FlowBoard Support Triage Agent loop.")
    parser.add_argument("--tickets-dir", default="tickets", help="Directory of ticket JSON files (default: tickets)")
    parser.add_argument("--outputs-dir", default="agent/outputs", help="Directory to save final drafts (default: agent/outputs)")
    parser.add_argument("--trajectories-dir", default="trajectories", help="Directory to save trajectory JSON logs (default: trajectories)")
    parser.add_argument("--queue-dir", default="agent/review_queue", help="Directory for review queue JSON files (default: agent/review_queue)")
    parser.add_argument("--model", default=None, help="LLM model name (defaults to active provider model)")
    parser.add_argument("--id", default=None, help="Process a single ticket ID (e.g. TKT-001)")
    args = parser.parse_args()

    run_all_tickets(
        tickets_dir=args.tickets_dir,
        outputs_dir=args.outputs_dir,
        trajectories_dir=args.trajectories_dir,
        queue_dir=args.queue_dir,
        model=args.model,
        single_id=args.id,
    )


if __name__ == "__main__":
    main()
