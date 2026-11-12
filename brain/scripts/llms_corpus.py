#!/usr/bin/env python3
"""
llms_corpus.py — ingest the machine-readable corpus docs.n8n.io publishes.

Why this exists: the GitHub repo (n8n-io/n8n-docs) is NOT a complete mirror of the
published site. Measured 2026-11-12: the repo clone yields 1348 pages, llms.txt lists
1408, and llms-full.txt carries 1402 real pages. Pages like
/connect/n8n-api/access-and-organization/users exist only on the site.

This module fetches llms.txt (title -> URL) and llms-full.txt (content, 14 parts),
splits the content on H1 boundaries while tracking code fences, and pairs each page
with its URL by title. Code-fence tracking matters: an env-var example contains lines
like "# n8n version - get the version number", and a naive split on H1 would cut a
real page in half there.

Stdlib only. Caches the result so repeated builds do not re-download 40 MB.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "brain" / "data" / "llms-pages.json"
LLMS_INDEX = "https://docs.n8n.io/llms.txt"
LLMS_FULL = "https://docs.n8n.io/llms-full.txt"
PARTS = 14
UA = {"User-Agent": "n8n-saas-factory-llms/1.0 (+https://github.com/homgorn/n8n-saas-factory)"}

# llms.txt lines look like: - [Title](https://docs.n8n.io/path.md): Description
# The description after the parenthesis is optional and varies, so it is not matched.
ENTRY_RE = re.compile(r"^-\s+\[(.+?)\]\((https://docs\.n8n\.io/\S+?\.md)\)", re.M)
H1_RE = re.compile(r"^#\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def fetch(url: str, timeout: int = 120, retries: int = 3) -> str:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {last}")


def fetch_index() -> dict[str, str]:
    """title -> published URL"""
    index = fetch(LLMS_INDEX)
    pairs = ENTRY_RE.findall(index)
    return {t.strip(): u for t, u in pairs}


def split_pages(body: str) -> list[tuple[str, str]]:
    """Split one corpus part into (heading, body) pairs, tracking code fences."""
    pages: list[tuple[str, str]] = []
    heading = ""
    buffer: list[str] = []
    in_fence = False

    for line in body.splitlines():
        is_fence = bool(FENCE_RE.match(line))
        if is_fence:
            in_fence = not in_fence
        if not in_fence:
            m = H1_RE.match(line)
            if m:
                if heading or any(b.strip() for b in buffer):
                    if heading:
                        pages.append((heading, "\n".join(buffer).strip()))
                heading = m.group(1).strip()
                buffer = []
                continue
        buffer.append(line)

    if heading and any(b.strip() for b in buffer):
        pages.append((heading, "\n".join(buffer).strip()))
    return pages


def fetch_corpus(timeout: int = 120) -> tuple[list[dict], dict]:
    """Return (pages, diagnostics). Each page: {title, url, body}."""
    title_to_url = fetch_index()
    pages: list[dict] = []
    seen_urls: set[str] = set()
    diagnostics = {"index_entries": len(title_to_url), "parts": PARTS, "parts_fetched": 0,
                   "headings_seen": 0, "unmatched_headings": 0, "bytes": 0}

    for part in range(PARTS):
        url = LLMS_FULL if part == 0 else f"{LLMS_FULL}/{part}"
        body = fetch(url, timeout=timeout)
        diagnostics["parts_fetched"] += 1
        diagnostics["bytes"] += len(body)
        for heading, text in split_pages(body):
            diagnostics["headings_seen"] += 1
            target = title_to_url.get(heading)
            if not target:
                diagnostics["unmatched_headings"] += 1
                continue
            if target in seen_urls:
                continue
            seen_urls.add(target)
            pages.append({"title": heading, "url": target, "body": text, "part": part})

    return pages, diagnostics


def load_or_fetch(use_cache: bool = True, timeout: int = 120) -> tuple[list[dict], dict]:
    if use_cache and CACHE.exists():
        payload = json.loads(CACHE.read_text(encoding="utf-8"))
        return payload["pages"], payload["diagnostics"]
    pages, diagnostics = fetch_corpus(timeout=timeout)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(
        json.dumps({"pages": pages, "diagnostics": diagnostics,
                    "fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    return pages, diagnostics


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Fetch the published llms corpus")
    ap.add_argument("--refresh", action="store_true", help="ignore the cache and re-fetch")
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args()

    pages, diagnostics = load_or_fetch(use_cache=not args.refresh, timeout=args.timeout)
    print(f"index entries     : {diagnostics['index_entries']}")
    print(f"parts fetched     : {diagnostics['parts_fetched']}/{diagnostics['parts']}")
    print(f"headings seen     : {diagnostics['headings_seen']}")
    print(f"unmatched headings: {diagnostics['unmatched_headings']}")
    print(f"pages captured    : {len(pages)}")
    print(f"bytes served      : {diagnostics['bytes']:,}")
    print(f"cache             : {CACHE}")


if __name__ == "__main__":
    main()
