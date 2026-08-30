"""
agent/llm_adapter.py — Unified Multi-Provider LLM Client for Anthropic & Groq.
"""
from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def _make_groq_client(api_key: str):
    """Create a Groq client. Uses httpx with verify=False only on local dev (not Vercel)."""
    from groq import Groq
    import httpx

    # Vercel has valid Linux SSL root certs; local Windows needs verify=False to prevent certificate errors
    is_vercel = bool(os.getenv("VERCEL") or os.getenv("VERCEL_ENV") or os.getenv("VERCEL_REGION"))

    if not is_vercel:
        return Groq(api_key=api_key, http_client=httpx.Client(verify=False))
    return Groq(api_key=api_key)


def get_llm_client():
    """Returns (provider, client, model) tuple for Groq or Anthropic."""
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        client = _make_groq_client(groq_key)
        return "groq", client, os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        import anthropic
        return "anthropic", anthropic.Anthropic(api_key=anthropic_key), os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

    raise ValueError("No API key configured. Please set GROQ_API_KEY or ANTHROPIC_API_KEY in .env.")
