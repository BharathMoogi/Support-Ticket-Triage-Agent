"""
Tool registry — maps Anthropic tool names to their Python callables.
Import this in agent/run.py to dispatch tool_use blocks.
"""
from tools.classify import classify_ticket
from tools.summarize import summarize_ticket
from tools.similar import find_similar
from tools.knowledge import search_knowledge_base
from tools.draft_reply import build_draft_context

TOOL_REGISTRY: dict[str, callable] = {
    "classify_ticket": classify_ticket,
    "summarize_ticket": summarize_ticket,
    "find_similar_tickets": find_similar,
    "search_knowledge_base": search_knowledge_base,
    "build_draft_context": build_draft_context,
}
