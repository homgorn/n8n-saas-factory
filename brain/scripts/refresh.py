#!/usr/bin/env python3
"""
refresh.py — compare the local wiki corpus against what docs.n8n.io actually serves.

This is the local half of the F008 sync loop. The n8n workflow (n8n-wiki/workflows/
f008-sync-workflow.json) runs on a schedule, fetches the machine-readable corpus and
computes the delta; this script applies the comparison to the wiki database and reports
what changed. Stdlib only, no API key.

Usage:
    python brain/scripts/refresh.py            # report only
    python brain/scripts/refresh.py --apply    # report, then rebuild changed pages
    python brain/scripts/refresh.py --timeout 60
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "brain" / "data" / "wiki.db"
INDEX = ROOT / "brain" / "index"
LLMS_INDEX = "https://docs.n8n.io/llms.txt"
LLMS_FULL = "https://docs.n8n.io/llms-full.txt"
PARTS = 14  # the corpus is paginated: base + /1 .. /13

UA = {"User-Agent": "n8n-saas-factory-refresh/1.0 (+https://github.com/homgorn/n8n-saas-factory)"}


def fetch(url: str, timeout: int = 60) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def live_pages(timeout: int) -> tuple[set[str], dict]:
    """Return (set of live doc URLs, diagnostics)."""
    diagnostics = {"index_ok": False, "parts_fetched": 0, "parts_failed": [], "bytes": 0}

    live: set[str] = set()

    # The index lists every page URL — cheap and authoritative for "what exists".
    try:
        index = fetch(LLMS_INDEX, timeout=timeout)
        diagnostics["index_ok"] = True
        diagnostics["bytes"] += len(index)
        for m in re.finditer(r"https://docs\.n8n\.io/[^\s\)\]]+", index):
            url = m.group(0).rstrip(".,)")
            if url.endswith(".md"):
                live.add(url.replace(".md", ""))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        diagnostics["index_error"] = f"{type(exc).__name__}: {exc}"

    # The full corpus confirms content freshness and its size.
    for part in range(PARTS):
        url = LLMS_FULL if part == 0 else f"{LLMS_FULL}/{part}"
        try:
            body = fetch(url, timeout=timeout)
            diagnostics["parts_fetched"] += 1
            diagnostics["bytes"] += len(body)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            diagnostics["parts_failed"].append({"part": part, "error": f"{type(exc).__name__}"})

    return live, diagnostics


def local_pages() -> dict[str, str]:
    """Return {source_url_without_md: content_hash} for the built corpus."""
    if not DB.exists():
        sys.exit(f"wiki database not found: {DB} — run forge.py build first")
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT source_url, content_hash FROM docs").fetchall()
    conn.close()
    return {url.replace(".md", ""): h for url, h in rows}


def main() -> None:
    ap = argparse.ArgumentParser(description="Compare the wiki corpus with docs.n8n.io")
    ap.add_argument("--apply", action="store_true", help="rebuild the wiki after reporting")
    ap.add_argument("--timeout", type=int, default=60)
    args = ap.parse_args()

    print(f"local corpus: {len(local_pages())} pages")
    print(f"fetching {LLMS_INDEX} and {PARTS} corpus parts …")
    live, diagnostics = live_pages(args.timeout)

    local = local_pages()
    live_urls = set(live)

    # GitBook section index files (README.md, SUMMARY.md) exist in the clone but are not
    # published pages, so llms.txt will never list them. Counting them as staleness would
    # produce a permanent false delta.
    def is_index_file(url: str) -> bool:
        tail = url.rstrip("/").rsplit("/", 1)[-1]
        return tail in ("README", "SUMMARY") or tail.endswith(".md")

    # Compare by slug, not by full path: n8n publishes some pages under a different
    # URL than the source file has (docs/build-your-first-workflow.md is served at
    # /get-started/build-your-first-workflow). Matching on the full path produced
    # permanent false staleness for those.
    def slug(url: str) -> str:
        return url.rstrip("/").rsplit("/", 1)[-1]

    live_slugs = {slug(u) for u in live_urls}
    local_slugs = {slug(u) for u in local}

    # GitBook publishes section folders as URLs too ("/administer/observe-and-log").
    # They are navigation, not pages, and would otherwise read as "new".
    source_docs = ROOT / "n8n-docs-source" / "docs"
    local_dirs = set()
    if source_docs.exists():
        for p in source_docs.rglob("*"):
            if p.is_dir():
                local_dirs.add(p.relative_to(source_docs).as_posix().lower())

    def is_section(url: str) -> bool:
        rel = url.replace("https://docs.n8n.io/", "").strip("/").lower()
        return rel in local_dirs

    new = sorted(
        u for u in live_urls
        if slug(u) not in local_slugs and not is_index_file(u) and not is_section(u)
    )
    # Local pages that docs.n8n.io does not publish (drafts, section readmes) are
    # informational, not staleness: nothing upstream can add them.
    unpublished = sorted(
        u for u in local
        if slug(u) not in live_slugs and not is_index_file(u)
    ) if live_urls else []

    report = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "diagnostics": diagnostics,
        "local_pages": len(local),
        "live_pages": len(live_urls),
        "new_on_docs_n8n_io": new[:200],
        "new_count": len(new),
        "unpublished_locally": unpublished[:200],
        "unpublished_count": len(unpublished),
        "corpus_bytes_served": diagnostics["bytes"],
        "in_sync": not new,
    }
    INDEX.mkdir(parents=True, exist_ok=True)
    (INDEX / "refresh-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print()
    print(f"live pages indexed by llms.txt : {len(live_urls)}")
    print(f"corpus parts fetched           : {diagnostics['parts_fetched']}/{PARTS}"
          f"{' (failed: ' + str(diagnostics['parts_failed']) + ')' if diagnostics['parts_failed'] else ''}")
    print(f"bytes served                   : {diagnostics['bytes']:,}")
    print(f"new pages on docs.n8n.io       : {len(new)}")
    for url in new[:10]:
        print(f"  + {url}")
    print(f"local pages not published live  : {len(unpublished)}")
    for url in unpublished[:10]:
        print(f"  - {url}")
    print(f"in sync                        : {report['in_sync']}")
    print(f"\nreport: {INDEX / 'refresh-report.json'}")

    if args.apply:
        if new:
            print("\n--apply: rebuilding the wiki from the local clone")
            import subprocess
            subprocess.run([sys.executable, str(ROOT / "brain" / "scripts" / "forge.py"), "build"], check=True)
        else:
            print("\n--apply: nothing to rebuild (corpus matches)")


if __name__ == "__main__":
    main()
