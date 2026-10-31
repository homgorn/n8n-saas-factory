#!/usr/bin/env python3
"""
query.py — LLM query interface for the n8n knowledge base (F002).

Classifies a natural-language question, retrieves the most relevant chunks and pages
from the wiki, and returns a structured response with citations, code examples,
related workflows, and next steps.

Usage:
    python brain/scripts/query.py "how do I paginate API results"
    python brain/scripts/query.py "how do I paginate API results" --format json
    python brain/scripts/query.py --interactive
    python brain/scripts/query.py --classify "why does my workflow fail at the If node"

The same module is importable: `from brain.scripts.query import answer, classify`
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "brain" / "data" / "wiki.db"
FORGE = ROOT / "brain" / "scripts" / "forge.py"
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "these", "those", "how", "what",
    "when", "where", "which", "who", "why", "does", "do", "did", "can", "could",
    "should", "would", "will", "you", "your", "are", "was", "were", "been", "being",
    "have", "has", "had", "into", "from", "about", "there", "their", "them", "then",
    "than", "also", "any", "all", "use", "using", "used", "get", "gets", "make",
    "need", "want", "like", "just", "only", "more", "most", "some", "such",
    "over", "under", "out", "off", "per", "via", "n8n", "node", "nodes",
}

# ---------------------------------------------------------------------------
# Query classification
# ---------------------------------------------------------------------------

QUERY_TYPES = {
    "how-to": "The user wants to accomplish a task. Answer with steps and code examples.",
    "node-ref": "The user wants reference documentation for a specific node. Answer with parameters, operations, and examples.",
    "troubleshooting": "The user has an error or unexpected behaviour. Answer with root cause and fix.",
    "architecture": "The user wants to understand how n8n works at a system level. Answer with concepts and diagrams.",
    "best-practice": "The user wants guidance on the right way to do something. Answer with recommendations and anti-patterns.",
}

# keyword sets for classification (ordered by specificity)
CLASSIFIER_PATTERNS = [
    # troubleshooting: error/fail/break/crash/not working
    (r"\b(fail|error|broken|crash|not working|doesn't work|won't|can't|unable|issue|problem|bug|debug|fix)\b",
     "troubleshooting"),
    # node-ref: "what parameters does X have", "X node", "reference"
    (r"\b(parameters?|reference|docs? for|what (does|is)|properties|options|operations|fields)\b",
     "node-ref"),
    # architecture: scale, design, how n8n works, architecture
    (r"\b(architect|scale|design|how (does|do) n8n|underlying|internals?|queue mode|database|concurrency)\b",
     "architecture"),
    # best-practice: best way, recommended, should I, pattern
    (r"\b(best (way|practice|approach)|recommended|should i|pattern|anti.?pattern|guideline)\b",
     "best-practice"),
    # how-to: default for action-oriented queries
    (r"\b(how (to|do|can|should)|create|build|set up|configure|implement|add|use|make)\b",
     "how-to"),
]


def classify(question: str) -> str:
    """Classify a question into one of QUERY_TYPES. Defaults to how-to."""
    q = question.lower()
    for pattern, qtype in CLASSIFIER_PATTERNS:
        if re.search(pattern, q):
            return qtype
    return "how-to"


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def search_chunks(question: str, limit: int = 8) -> list[dict]:
    """IDF-ranked chunk search with heading boost (same as forge.py ask)."""
    terms = [w for w in re.findall(r"[a-z0-9_]+", question.lower())
             if len(w) > 2 and w not in STOPWORDS]
    if not terms:
        return []

    conn = _conn()
    total = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] or 1
    idf = {}
    for t in terms:
        df = conn.execute("SELECT COUNT(*) FROM chunks WHERE lower(text) LIKE ?",
                          (f"%{t}%",)).fetchone()[0]
        idf[t] = max(0.05, math.log(1 + total / max(1, df)))

    word_re = {t: re.compile(rf"\b{re.escape(t)}\b", re.I) for t in terms}
    scores: Counter = Counter()
    best: dict[str, dict] = {}

    for term, weight in idf.items():
        rx = word_re[term]
        rows = conn.execute(
            "SELECT chunk_id, doc_id, heading, kind, text FROM chunks WHERE lower(text) LIKE ?",
            (f"%{term}%",),
        ).fetchall()
        for r in rows:
            hits = len(rx.findall(r["text"]))
            if not hits:
                continue
            in_heading = 12 if rx.search(r["heading"] or "") else 0
            body = 1 + math.log(hits)
            scores[r["chunk_id"]] += weight * (body + in_heading)
            if r["chunk_id"] not in best:
                best[r["chunk_id"]] = dict(r)

        # title boost
        for slug, title in conn.execute(
                "SELECT slug, title FROM docs WHERE lower(title) LIKE ?", (f"%{term}%",)):
            if rx.search(title):
                scores[f"title::{slug}"] += weight * 20

    results = []
    for cid, score in scores.most_common(limit):
        if cid.startswith("title::"):
            slug = cid.split("::", 1)[1]
            row = conn.execute(
                "SELECT slug, title, summary, source_url, difficulty FROM docs WHERE slug=?",
                (slug,)).fetchone()
            if row:
                results.append({
                    "type": "page",
                    "slug": row["slug"],
                    "title": row["title"],
                    "summary": row["summary"],
                    "source_url": row["source_url"],
                    "difficulty": row["difficulty"],
                    "score": round(score, 2),
                })
        else:
            b = best[cid]
            row = conn.execute(
                "SELECT slug, title, source_url, difficulty FROM docs WHERE doc_id=?",
                (b["doc_id"],)).fetchone()
            if row:
                results.append({
                    "type": "chunk",
                    "chunk_id": b["chunk_id"],
                    "title": row["title"],
                    "slug": row["slug"],
                    "heading": b["heading"],
                    "kind": b["kind"],
                    "text": b["text"],
                    "source_url": row["source_url"],
                    "difficulty": row["difficulty"],
                    "score": round(score, 2),
                })
    conn.close()
    return results


def get_page(slug: str) -> dict | None:
    """Fetch full page metadata by slug."""
    conn = _conn()
    row = conn.execute(
        "SELECT slug, title, summary, source_url, difficulty, content_type, words, chunk_count "
        "FROM docs WHERE slug=?", (slug,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_code_examples(slug: str, limit: int = 5) -> list[dict]:
    """Extract code blocks from a page's chunks."""
    conn = _conn()
    rows = conn.execute(
        "SELECT text, heading, kind FROM chunks WHERE doc_id IN "
        "(SELECT doc_id FROM docs WHERE slug=?) AND kind='code_example' LIMIT ?",
        (slug, limit)).fetchall()
    conn.close()
    return [{"heading": r["heading"], "code": r["text"], "kind": r["kind"]} for r in rows]


def get_related_workflows(question: str, limit: int = 3) -> list[dict]:
    """Find workflow JSON files relevant to the question."""
    terms = [w for w in re.findall(r"[a-z0-9_]+", question.lower())
             if len(w) > 2 and w not in STOPWORDS]
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT slug, name, node_count, node_types, trigger_type, credentials "
            "FROM workflows").fetchall()
    except sqlite3.OperationalError:
        conn.close()
        return []
    scored = []
    for r in rows:
        text = (r["name"] + " " + r["node_types"] + " " + (r["trigger_type"] or "")).lower()
        score = sum(1 for t in terms if t in text)
        if score > 0:
            scored.append((score, dict(r)))
    scored.sort(key=lambda x: -x[0])
    conn.close()
    return [s[1] for s in scored[:limit]]


# ---------------------------------------------------------------------------
# Response formatting
# ---------------------------------------------------------------------------

def answer(question: str) -> dict:
    """Full structured answer for a question."""
    qtype = classify(question)
    results = search_chunks(question, limit=8)
    code_examples = []
    related_workflows = get_related_workflows(question, limit=3)

    # Collect code examples from top chunk results
    seen_slugs = set()
    for r in results:
        if r["type"] == "chunk" and r["slug"] not in seen_slugs:
            seen_slugs.add(r["slug"])
            examples = get_code_examples(r["slug"], limit=2)
            code_examples.extend(examples)
            if len(code_examples) >= 5:
                break

    # Build citation list (unique pages)
    citations = []
    seen = set()
    for r in results:
        key = r["slug"]
        if key not in seen:
            seen.add(key)
            citations.append({
                "title": r["title"],
                "url": r["source_url"],
                "difficulty": r.get("difficulty", "intermediate"),
            })

    # Build response
    response = {
        "question": question,
        "query_type": qtype,
        "query_type_description": QUERY_TYPES[qtype],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "citations": citations,
        "code_examples": code_examples[:5],
        "related_workflows": related_workflows,
        "next_steps": _next_steps(qtype, results),
    }
    return response


def _next_steps(qtype: str, results: list[dict]) -> list[str]:
    """Generate actionable next steps based on query type and results."""
    steps = []
    if qtype == "how-to":
        steps.append("Try the example in the n8n editor: https://app.n8n.cloud/register")
        steps.append("Check the workflow templates: https://n8n.io/workflows/")
    elif qtype == "node-ref":
        steps.append("Open the node in n8n to see all parameters and operations")
        steps.append("Test with sample data using the 'Execute step' button")
    elif qtype == "troubleshooting":
        steps.append("Check execution logs: Executions tab in n8n")
        steps.append("Run a security audit: Settings > Security in n8n")
    elif qtype == "architecture":
        steps.append("Read the architecture docs: https://docs.n8n.io/deploy/host-n8n/understand-the-architecture/")
    elif qtype == "best-practice":
        steps.append("Review the n8n community forum for real-world patterns")

    # Add related page suggestions
    if results:
        top = results[0]
        steps.append(f"Read more: {top['title']} ({top['source_url']})")
    return steps


def format_text(response: dict) -> str:
    """Human-readable text format."""
    lines = []
    lines.append(f"## {response['question']}")
    lines.append(f"Type: {response['query_type']} — {response['query_type_description']}")
    lines.append("")

    # Top result summary
    if response["results"]:
        top = response["results"][0]
        lines.append(f"### Top result: {top['title']}")
        if top["type"] == "chunk":
            lines.append(f"Section: {top['heading']}")
            text = re.sub(r"\s+", " ", top["text"])[:400]
            lines.append(f"{text}…")
        lines.append(f"Source: {top['source_url']}")
        lines.append("")

    # Citations
    if response["citations"]:
        lines.append("### Sources")
        for c in response["citations"]:
            lines.append(f"- [{c['title']}]({c['url']}) ({c['difficulty']})")
        lines.append("")

    # Code examples
    if response["code_examples"]:
        lines.append("### Code examples")
        for ex in response["code_examples"]:
            lines.append(f"#### {ex['heading']}")
            lines.append("```")
            lines.append(ex["code"][:500])
            lines.append("```")
            lines.append("")

    # Related workflows
    if response["related_workflows"]:
        lines.append("### Related workflows")
        for w in response["related_workflows"]:
            lines.append(f"- {w['name']} ({w['node_count']} nodes, {w['trigger_type']})")
        lines.append("")

    # Next steps
    if response["next_steps"]:
        lines.append("### Next steps")
        for s in response["next_steps"]:
            lines.append(f"1. {s}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Query the n8n knowledge base")
    ap.add_argument("question", nargs="?", help="natural language question")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--classify", help="classify a question without searching")
    ap.add_argument("--interactive", action="store_true", help="interactive REPL")
    args = ap.parse_args()

    if args.classify:
        print(f"Query type: {classify(args.classify)}")
        print(f"Description: {QUERY_TYPES[classify(args.classify)]}")
        return

    if args.interactive:
        print("n8n Knowledge Base — Interactive Query (type 'quit' to exit)")
        while True:
            try:
                q = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if q.lower() in ("quit", "exit", "q"):
                break
            if not q:
                continue
            resp = answer(q)
            print(format_text(resp))
        return

    if not args.question:
        ap.error("provide a question or use --interactive")

    resp = answer(args.question)
    if args.format == "json":
        print(json.dumps(resp, indent=2, ensure_ascii=False))
    else:
        print(format_text(resp))


if __name__ == "__main__":
    main()