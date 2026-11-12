"""Shared retrieval scoring.

forge.py's `ask` and query.py's `search_chunks` used to carry two copies of the
same ranking rules, which is how they drifted apart. Both now call `score_chunks`.

Title matching is graded, not flat:

    exact title match      x40
    title starts with term x20
    title contains term    x8

A flat x20 for any title substring is what let "Cisco Secure Endpoint" outrank
the page titled "Webhook" for the query "how to build a webhook endpoint":
"endpoint" is a weak term but scored as if it were strong.
"""

from __future__ import annotations

import math
import re
import sqlite3
from collections import Counter, defaultdict

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "these", "those", "how", "what",
    "when", "where", "which", "who", "why", "does", "do", "did", "can", "could",
    "should", "would", "will", "you", "your", "are", "was", "were", "been", "being",
    "have", "has", "had", "into", "from", "about", "there", "their", "them", "then",
    "than", "also", "any", "all", "use", "using", "used", "get", "gets", "make",
    "need", "want", "like", "just", "only", "more", "most", "some", "such",
    "over", "under", "out", "off", "per", "via", "n8n", "node", "nodes",
}

TITLE_EXACT = 40
TITLE_PREFIX = 25
TITLE_CONTAINS = 6
# Ceiling on one term's contribution to a document's score. Low enough that one rare term
# cannot win outright, high enough that a page matching two terms still beats a page matching
# one term that happens to sit at the ceiling.
MAX_TERM_SCORE = 70.0
# A heading match is weaker evidence than a title match: a chunk whose heading happens to
# mention a term is not necessarily a page about that term. At 12 the Docker Compose
# deployment page outranked "Environment variables" for an environment-variables query.
HEADING_BOOST = 5


def tokenize(question: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9_]+", question.lower())
            if len(w) > 2 and w not in STOPWORDS]


def inverse_document_frequency(conn: sqlite3.Connection, terms: list[str]) -> dict[str, float]:
    total = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] or 1
    idf: dict[str, float] = {}
    for term in terms:
        df = conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE lower(text) LIKE ?", (f"%{term}%",)
        ).fetchone()[0]
        idf[term] = max(0.05, math.log(1 + total / max(1, df)))
    return idf


def title_score(title: str, term: str) -> float:
    t = title.lower().strip()
    if t == term:
        return TITLE_EXACT
    if t.startswith(term):
        return TITLE_PREFIX
    if term in t:
        return TITLE_CONTAINS
    return 0.0


def score_chunks(
    conn: sqlite3.Connection,
    question: str,
    limit: int = 10,
) -> tuple[list[dict], Counter]:
    """Return (results, scores). Results are dicts with id/score/payload-ish fields."""
    terms = tokenize(question)
    if not terms:
        return [], Counter()

    idf = inverse_document_frequency(conn, terms)
    word_re = {t: re.compile(rf"\b{re.escape(t)}\b", re.I) for t in terms}

    scores: Counter = Counter()
    per_term: dict[str, Counter] = {t: Counter() for t in terms}
    best: dict[str, dict] = {}

    for term, weight in idf.items():
        rx = word_re[term]
        rows = conn.execute(
            "SELECT chunk_id, doc_id, heading, kind, text FROM chunks WHERE lower(text) LIKE ?",
            (f"%{term}%",),
        ).fetchall()
        for chunk_id, doc_id, heading, kind, text in rows:
            hits = len(rx.findall(text))
            if not hits:
                continue
            in_heading = HEADING_BOOST if rx.search(heading or "") else 0
            # Diminishing returns: the 10th mention says much less than the 2nd.
            body = 1 + math.log(hits)
            # Length normalisation. A code block can mention a term 30 times across 2000
            # tokens; a page that is about the term mentions it 5 times in 100 tokens.
            # Without this, long code chunks outrank the actually relevant page.
            tokens = max(1, len(text) // 4)
            density = 1.0 / (1.0 + math.log(1 + tokens / 400))
            per_term[term][chunk_id] += weight * (body * density + in_heading)
            best.setdefault(chunk_id, {
                "chunk_id": chunk_id, "doc_id": doc_id,
                "heading": heading, "kind": kind, "text": text,
            })

    # Titles are graded by how exactly they match the term.
    for term, weight in idf.items():
        for slug, title in conn.execute("SELECT slug, title FROM docs"):
            ts = title_score(title, term)
            if ts:
                per_term[term][f"title::{slug}"] += weight * ts

    # Soft ceiling on what a single term can contribute. A hard cap flattened documents that
    # were genuinely better ("Webhook" and a page titled "Build" both landed on the cap and
    # the tie was broken by insertion order). Saturating instead of clipping keeps the
    # ordering meaningful while still stopping one rare term from winning outright.
    matched_terms: dict[str, set[str]] = defaultdict(set)
    for term, contributions in per_term.items():
        for cid, value in contributions.items():
            capped = MAX_TERM_SCORE * (1 - math.exp(-value / MAX_TERM_SCORE))
            scores[cid] += capped
            matched_terms[cid].add(term)

    # Coordination as a multiplier, not as a primary sort key. A page matching several query
    # terms gets up to ~2.4x, but the base score still decides: otherwise a release-notes page
    # that happens to contain all five words of a query outranks the page actually about them.
    for cid in list(scores):
        extra = max(0, len(matched_terms.get(cid, ())) - 1)
        scores[cid] *= 1 + 0.35 * extra

    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)

    results = []
    for cid, score in ordered[:limit]:
        if cid.startswith("title::"):
            slug = cid.split("::", 1)[1]
            row = conn.execute(
                "SELECT slug, title, summary, source_url, difficulty FROM docs WHERE slug=?",
                (slug,),
            ).fetchone()
            if row:
                results.append({
                    "type": "page", "slug": row[0], "title": row[1],
                    "summary": row[2], "source_url": row[3],
                    "difficulty": row[4], "score": round(score, 2),
                })
        elif cid in best:
            b = best[cid]
            row = conn.execute(
                "SELECT slug, title, source_url, difficulty FROM docs WHERE doc_id=?",
                (b["doc_id"],),
            ).fetchone()
            if row:
                results.append({
                    "type": "chunk", "chunk_id": cid, "title": row[1],
                    "slug": row[0], "heading": b["heading"], "kind": b["kind"],
                    "text": b["text"], "source_url": row[2],
                    "difficulty": row[3], "score": round(score, 2),
                })

    return results, scores
