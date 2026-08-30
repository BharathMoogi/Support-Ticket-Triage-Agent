"""
agent/retrieval.py — Documentation Chunking & TF-IDF Vector Search.

Design Choice Explanation:
---------------------------
We use a pure-Python & NumPy TF-IDF (Term Frequency - Inverse Document Frequency)
vector search engine over external embeddings APIs (e.g. Voyage / OpenAI) for three reasons:
1. Zero Latency & Offline Independence: Fully local and deterministic with zero API roundtrips
   or external rate-limit bottlenecks during agent loops.
2. Exact Technical Term Matching: Excellent precision on domain-specific keywords and identifiers
   (e.g., 'ERR_WS_DISCONNECTED_502', 'SAML', 'TOTP', 'IndexedDB', '14-day', 'VAT') which embeddings
   frequently smooth out or misrank.
3. Lightweight & Dependency-Free: Built with NumPy (<100 LOC of vector math) without heavy vector
   database infrastructure.
"""

from __future__ import annotations

import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Stop words & Tokenizer
# ---------------------------------------------------------------------------

STOP_WORDS = frozenset(
    "a an the and or but in on at to for of with is are was were be been "
    "being have has had do does did will would could should may might "
    "i me my we our you your he she it its they their this that these "
    "those what which who whom when where why how not no if can".split()
)


def tokenize(text: str) -> list[str]:
    """
    Extract alphanumeric words, technical identifiers, and terms with dashes/dots.
    Lowercases and filters common stop words.
    """
    # Keep words, numbers, and tech codes (e.g. 502, saml, totp, sha256)
    tokens = re.findall(r"[a-z0-9_]+(?:-[a-z0-9_]+)*", text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


# ---------------------------------------------------------------------------
# Chunking Strategy (~150-250 words per chunk, preserving heading context)
# ---------------------------------------------------------------------------

@dataclass
class DocChunk:
    chunk_id: str
    doc_name: str
    section_heading: str
    content: str
    word_count: int


def chunk_markdown_file(filepath: Path, target_words: int = 200) -> list[DocChunk]:
    """
    Chunk a single markdown document into logical blocks based on headers
    and paragraphs, maintaining section context for each chunk.
    """
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    chunks: list[DocChunk] = []
    doc_name = filepath.name
    current_h1 = ""
    current_h2 = ""
    buffer: list[str] = []
    chunk_idx = 0

    def flush_buffer(heading: str) -> None:
        nonlocal chunk_idx, buffer
        if not buffer:
            return
        content = "\n".join(buffer).strip()
        words = len(content.split())
        if words > 5:
            full_heading = f"{current_h1} > {heading}".strip(" >")
            chunks.append(
                DocChunk(
                    chunk_id=f"{doc_name}#chunk_{chunk_idx}",
                    doc_name=doc_name,
                    section_heading=full_heading,
                    content=content,
                    word_count=words,
                )
            )
            chunk_idx += 1
        buffer = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            flush_buffer(current_h2 or current_h1)
            current_h1 = stripped[2:].strip()
            current_h2 = ""
            buffer.append(line)
        elif stripped.startswith("## "):
            flush_buffer(current_h2 or current_h1)
            current_h2 = stripped[3:].strip()
            buffer.append(f"### Section: {current_h2}")
        else:
            buffer.append(line)
            # If current buffer exceeds target words and hits a blank line, split
            if not stripped and len(" ".join(buffer).split()) >= target_words:
                flush_buffer(current_h2 or current_h1)

    flush_buffer(current_h2 or current_h1)
    return chunks


# ---------------------------------------------------------------------------
# TF-IDF Vector Search Index
# ---------------------------------------------------------------------------

class DocSearchIndex:
    """In-memory TF-IDF index over documentation chunks using NumPy."""

    def __init__(self, chunks: list[DocChunk]) -> None:
        self.chunks = chunks
        self.vocabulary: dict[str, int] = {}
        self.idf: np.ndarray = np.array([])
        self.matrix: np.ndarray = np.array([])
        self._build_index()

    def _build_index(self) -> None:
        if not self.chunks:
            return

        tokenized_corpus: list[list[str]] = []
        df_counts: Counter[str] = Counter()

        for chunk in self.chunks:
            # Combine heading context and content for indexing
            text = f"{chunk.section_heading} {chunk.content}"
            tokens = tokenize(text)
            tokenized_corpus.append(tokens)
            df_counts.update(set(tokens))

        # Build vocabulary sorted by term
        vocab_terms = sorted(df_counts.keys())
        self.vocabulary = {term: idx for idx, term in enumerate(vocab_terms)}
        num_docs = len(self.chunks)
        num_terms = len(vocab_terms)

        # Compute smoothed IDF: log((N + 1) / (DF + 1)) + 1
        self.idf = np.zeros(num_terms, dtype=np.float32)
        for term, idx in self.vocabulary.items():
            df = df_counts[term]
            self.idf[idx] = math.log((num_docs + 1.0) / (df + 1.0)) + 1.0

        # Build TF-IDF document matrix (num_docs x num_terms)
        self.matrix = np.zeros((num_docs, num_terms), dtype=np.float32)
        for doc_idx, tokens in enumerate(tokenized_corpus):
            if not tokens:
                continue
            tf_counts = Counter(tokens)
            total_tokens = len(tokens)
            for term, count in tf_counts.items():
                if term in self.vocabulary:
                    term_idx = self.vocabulary[term]
                    tf = count / total_tokens
                    self.matrix[doc_idx, term_idx] = tf * self.idf[term_idx]

        # L2-normalize document vectors for cosine similarity
        norms = np.linalg.norm(self.matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.matrix = self.matrix / norms

    def search(self, query: str, k: int = 3) -> list[dict[str, Any]]:
        """Search the index for query and return top-k scored chunks."""
        if not self.chunks or not self.vocabulary:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        query_vector = np.zeros(len(self.vocabulary), dtype=np.float32)
        tf_counts = Counter(query_tokens)
        total_tokens = len(query_tokens)

        for term, count in tf_counts.items():
            if term in self.vocabulary:
                idx = self.vocabulary[term]
                tf = count / total_tokens
                query_vector[idx] = tf * self.idf[idx]

        query_norm = np.linalg.norm(query_vector)
        if query_norm == 0:
            return []
        query_vector = query_vector / query_norm

        # Cosine similarity via matrix-vector multiplication
        scores = np.dot(self.matrix, query_vector)
        top_indices = np.argsort(scores)[::-1][:k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score <= 0.0:
                continue
            chunk = self.chunks[idx]
            results.append(
                {
                    "doc_name": chunk.doc_name,
                    "chunk_id": chunk.chunk_id,
                    "heading": chunk.section_heading,
                    "score": round(score, 4),
                    "content": chunk.content,
                }
            )
        return results


# Global cached index instance
_GLOBAL_INDEX: DocSearchIndex | None = None
_INDEX_DOCS_DIR: str | None = None


def get_or_build_index(docs_dir: str | Path = "docs") -> DocSearchIndex:
    """Get the cached search index or build it if not already loaded."""
    global _GLOBAL_INDEX, _INDEX_DOCS_DIR
    docs_path = Path(docs_dir)
    dir_str = str(docs_path.resolve())

    if _GLOBAL_INDEX is None or _INDEX_DOCS_DIR != dir_str:
        chunks: list[DocChunk] = []
        if docs_path.exists() and docs_path.is_dir():
            for file in sorted(docs_path.glob("*.md")):
                # Skip anything that is not a regular file (safety guard)
                if file.is_file():
                    chunks.extend(chunk_markdown_file(file))
        _GLOBAL_INDEX = DocSearchIndex(chunks)
        _INDEX_DOCS_DIR = dir_str

    return _GLOBAL_INDEX


def search_docs(query: str, k: int = 3, docs_dir: str | Path = "docs") -> list[dict[str, Any]]:
    """
    Search documentation articles for relevant chunks.

    Args:
        query: Search string or ticket text.
        k: Number of top chunks to return (default: 3).
        docs_dir: Directory containing markdown documentation (default: 'docs').

    Returns:
        List of matching dicts with keys: doc_name, chunk_id, heading, score, content.
    """
    index = get_or_build_index(docs_dir)
    return index.search(query, k=k)


# ---------------------------------------------------------------------------
# Sanity Check & Self Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    # Ensure stdout handles UTF-8 cleanly on Windows
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    from rich.console import Console
    from rich.panel import Panel

    console = Console(highlight=False)
    console.print("[bold green]=== Testing Documentation Retrieval Engine ===[/bold green]\n")

    test_queries = [
        "How do I export my board cards and assignees to CSV or Excel?",
        "What is the refund policy for annual subscription renewals?",
        "WebSocket connection to wss://sync.flowboard.app failed with 502 error",
        "How do I configure SAML Okta Single Sign On ACS URL on Team tier?",
        "Where can I add our company VAT number to past invoices?",
    ]

    for q in test_queries:
        console.rule(f"[bold cyan]Query: '{q}'[/bold cyan]")
        results = search_docs(q, k=2)
        if not results:
            console.print("[yellow]No relevant chunks found.[/yellow]\n")
            continue

        for r in results:
            panel_content = (
                f"[bold magenta]File:[/bold magenta] {r['doc_name']} ({r['chunk_id']})\n"
                f"[bold magenta]Section:[/bold magenta] {r['heading']}\n"
                f"[bold magenta]Similarity Score:[/bold magenta] {r['score']}\n\n"
                f"{r['content']}"
            )
            console.print(Panel(panel_content, border_style="blue"))
        console.print()
