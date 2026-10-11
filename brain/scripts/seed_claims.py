#!/usr/bin/env python3
"""
seed_claims.py — record the first provenance-stamped claims.

A claim only reaches a wiki page or a README if it lives here with a type and a source.
Types: measured | reported | inferred | unconfirmed

Usage: python brain/scripts/seed_claims.py
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "brain" / "data" / "wiki.db"
INDEX = ROOT / "brain" / "index"

CLAIMS = [
    {
        "id": "licence-sustainable-use",
        "kind": "reported",
        "text": (
            "n8n is licensed under the Sustainable Use License, not MIT. Use is limited to the "
            "licensor's internal business purposes or non-commercial/personal use, and "
            "distribution or provision to others must be free of charge and non-commercial."
        ),
        "source": "https://github.com/n8n-io/n8n/blob/master/LICENSE.md",
        "observed_at": "2026-10-12",
        "doc_id": None,
    },
    {
        "id": "licence-hosted-saas-not-permitted",
        "kind": "inferred",
        "text": (
            "Offering a paid SaaS that hosts n8n for customers, or embeds it so customers drive it, "
            "falls outside the Sustainable Use License grant. The product must instead call a "
            "n8n instance the customer operates under their own licence, or be sold under a "
            "separate OEM agreement."
        ),
        "source": "brain/decisions/ADR-001-n8n-licence-blocks-hosted-saas.md",
        "observed_at": "2026-10-12",
        "doc_id": None,
    },
    {
        "id": "licence-customer-n8n-cloud-unresolved",
        "kind": "unconfirmed",
        "text": (
            "Whether a customer on n8n Cloud who connects to our product via webhook counts as the "
            "licensor 'providing n8n to others' is not resolved. Needs a legal opinion."
        ),
        "source": None,
        "observed_at": "2026-10-12",
        "doc_id": None,
    },
    {
        "id": "docs-corpus-shape",
        "kind": "measured",
        "text": (
            "The cloned n8n docs contain 1,348 markdown pages, 9,578 chunks and 688,466 words "
            "across 11 domains, plus 12 importable workflow JSON files."
        ),
        "source": "brain/data/wiki.db :: docs, chunks, workflows",
        "observed_at": "2026-10-12",
        "doc_id": None,
    },
    {
        "id": "docs-source-of-truth",
        "kind": "reported",
        "text": (
            "The documentation is generated from github.com/n8n-io/n8n-docs, a GitBook space. "
            "Cloning that repo gives markdown source rather than scraped HTML, and n8n also "
            "publishes a machine-readable corpus at docs.n8n.io/llms-full.txt and an index at "
            "docs.n8n.io/llms.txt."
        ),
        "source": "https://github.com/n8n-io/n8n-docs",
        "observed_at": "2026-10-12",
        "doc_id": None,
    },
    {
        "id": "fts-ranking-uses-idf",
        "kind": "measured",
        "text": (
            "forge.py ask ranks chunks by inverse document frequency with word-boundary matching. "
            "An earlier substring-count implementation returned irrelevant results for the query "
            "'how do I paginate API results', scoring a deployment page above the HTTP Request "
            "pagination section."
        ),
        "source": "brain/scripts/forge.py :: ask()",
        "observed_at": "2026-10-12",
        "doc_id": None,
    },
    {
        "id": "vector-search-not-wired",
        "kind": "measured",
        "text": (
            "Semantic/vector retrieval is not available. The wiki is queryable through SQLite FTS5 "
            "and the JSON indexes only; the Qdrant pipeline in saas-factory/analyzer requires "
            "OPENAI_API_KEY and a running Qdrant instance."
        ),
        "source": "brain/HANDOFF.md",
        "observed_at": "2026-10-12",
        "doc_id": None,
    },
]


def main() -> None:
    if not DB.exists():
        raise SystemExit(f"database not found: {DB} — run forge.py build first")
    now = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            kind TEXT NOT NULL,
            source TEXT,
            observed_at TEXT,
            doc_id TEXT,
            recorded_at TEXT NOT NULL
        )
    """)
    # forge.py owns the table and may have created it without recorded_at; add it if so
    existing = {row[1] for row in conn.execute("PRAGMA table_info(claims)")}
    if "recorded_at" not in existing:
        conn.execute("ALTER TABLE claims ADD COLUMN recorded_at TEXT")

    for claim in CLAIMS:
        conn.execute(
            """INSERT OR REPLACE INTO claims (id, text, kind, source, observed_at, doc_id, recorded_at)
               VALUES (?,?,?,?,?,?,?)""",
            (claim["id"], claim["text"], claim["kind"], claim["source"],
             claim["observed_at"], claim["doc_id"], now),
        )
    conn.commit()

    rows = conn.execute("SELECT id, kind, source FROM claims ORDER BY kind, id").fetchall()
    conn.close()

    INDEX.mkdir(parents=True, exist_ok=True)
    (INDEX / "claims.json").write_text(
        json.dumps(
            {
                "generated": now,
                "types": {
                    "measured": "ran it, the artifact is named",
                    "reported": "a source says it, URL + retrieval date",
                    "inferred": "reasoned it, the reasoning is written out",
                    "unconfirmed": "looked for it, not found",
                },
                "claims": [
                    {"id": c["id"], "type": c["kind"], "source": c["source"], "observed_at": c["observed_at"],
                     "text": c["text"]}
                    for c in CLAIMS
                ],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"recorded {len(rows)} claims")
    for cid, kind, source in rows:
        print(f"  [{kind:<12}] {cid}")
        if source:
            print(f"               {source}")


if __name__ == "__main__":
    main()