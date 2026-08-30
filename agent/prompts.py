"""
System prompt and Anthropic tool schemas for the Ticket Triage Agent.
Keep all prompt text here so run.py stays logic-only.
"""

SYSTEM_PROMPT = """\
You are an expert support-ticket triage agent. Your job is to:
1. Understand the customer's issue fully.
2. Classify the ticket (category, priority, sentiment).
3. Find similar past tickets and relevant knowledge-base articles.
4. Draft a clear, empathetic reply that resolves the issue or sets the right expectations.

You have access to the following tools — use them in order:
  1. classify_ticket      → understand category/priority/sentiment
  2. summarize_ticket     → condense long bodies before searching
  3. find_similar_tickets → find historical context
  4. search_knowledge_base → find help articles
  5. build_draft_context  → assemble all context into a structured bundle

After calling build_draft_context, write the final human-review draft as plain text.
Be concise, professional, and empathetic. Never make up facts not in the context.
"""

# ---------------------------------------------------------------------------
# Anthropic tool schemas (passed as the `tools` parameter to messages.create)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "classify_ticket",
        "description": (
            "Classify a support ticket. Returns category, priority (P1–P4), "
            "and customer sentiment (positive/neutral/negative/frustrated)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Ticket subject line"},
                "body": {"type": "string", "description": "Full ticket body text"},
            },
            "required": ["subject", "body"],
        },
    },
    {
        "name": "summarize_ticket",
        "description": (
            "Summarise a potentially long ticket body into ≤300 characters "
            "to use as a compact search query."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "body": {"type": "string", "description": "Full ticket body text"},
            },
            "required": ["body"],
        },
    },
    {
        "name": "find_similar_tickets",
        "description": (
            "Search historical resolved tickets by keyword similarity. "
            "Returns up to top_k matches with their resolutions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Short search query (use summarize_ticket output)",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Max number of results (1–5)",
                    "default": 3,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_knowledge_base",
        "description": (
            "Search the internal knowledge base for help articles relevant "
            "to the customer's issue."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search terms derived from the ticket",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "build_draft_context",
        "description": (
            "Assemble all gathered information into a structured context bundle "
            "that you will use to write the final reply draft."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Condensed ticket summary"},
                "classification": {
                    "type": "object",
                    "description": "Output from classify_ticket",
                    "properties": {
                        "category": {"type": "string"},
                        "priority": {"type": "string"},
                        "sentiment": {"type": "string"},
                    },
                },
                "similar_tickets": {
                    "type": "array",
                    "description": "List of similar resolved tickets",
                    "items": {"type": "object"},
                },
                "kb_articles": {
                    "type": "array",
                    "description": "List of relevant KB articles",
                    "items": {"type": "object"},
                },
            },
            "required": ["summary", "classification"],
        },
    },
]
