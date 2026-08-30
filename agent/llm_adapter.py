"""
agent/llm_adapter.py — Unified Multi-Provider LLM Client for Anthropic & Groq.
"""
from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def get_llm_client():
    """Returns an active LLM client (Groq or Anthropic)."""
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        import httpx
        from groq import Groq
        http_client = httpx.Client(verify=False)
        return "groq", Groq(api_key=groq_key, http_client=http_client), os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        import anthropic
        return "anthropic", anthropic.Anthropic(api_key=anthropic_key), os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

    raise ValueError("No API key configured. Please set GROQ_API_KEY or ANTHROPIC_API_KEY in .env.")
