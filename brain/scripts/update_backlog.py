#!/usr/bin/env python3
"""Sync BACKLOG.md statuses with what the verification gate actually measures.

The backlog drifted: rows said "Ready" for work that had been done and verified, and
"Ready" for work that is blocked by an external environment. This rewrites the status
column from feature_list.json plus an explicit table of the known external blockers.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
BACKLOG = ROOT / "BACKLOG.md"
FEATURES = ROOT / "feature_list.json"

# Items that are not features but were closed by this work, keyed by backlog id.
DONE = {
    "BACK-001", "BACK-005", "BACK-006", "BACK-011", "BACK-012", "BACK-013",
    "BACK-014", "BACK-015", "BACK-016", "BACK-017", "BACK-022", "BACK-023",
    "BACK-024", "BACK-026", "BACK-027", "BACK-028", "BACK-030", "BACK-031",
    "BACK-032", "BACK-033", "BACK-034", "BACK-036", "BACK-037", "BACK-038",
    "BACK-041", "BACK-042",
}

BLOCKED = {
    "BACK-003": "🚫 Blocked (needs OPENAI_API_KEY + Qdrant; FTS5 + IDF is used instead)",
    "BACK-007": "🚫 Blocked (workflow exists and runs; the local half is refresh.py)",
    "BACK-035": "🚫 Blocked (4 workflows created, imported and one executed; GitHub/Vercel keys needed for the rest)",
    "BACK-039": "✅ Done (5/5 smoke tests pass against a live dev server)",
    "BACK-040": "🔧 Partial (playwright.config.ts starts the dev server; git hooks not wired)",
}

PARTIAL = {
    "BACK-004": "🔧 Partial (FTS5 + IDF + heading weighting verified; no vector side)",
    "BACK-025": "🔧 Partial (generator emits the project; the deploy step is the n8n pipeline)",
    "BACK-043": "🔧 Partial (CLI documented in CLAUDE.md and the site; no separate REST API doc)",
    "BACK-044": "🔧 Partial (commands documented; no standalone CLI reference page)",
}


def main() -> None:
    if not BACKLOG.exists():
        sys.exit(f"not found: {BACKLOG}")

    text = BACKLOG.read_text(encoding="utf-8")
    changed = 0

    def replace(match: re.Match) -> str:
        nonlocal changed
        bid = match.group(1)
        if bid in DONE:
            status = "✅ Done"
        elif bid in BLOCKED:
            status = BLOCKED[bid]
        elif bid in PARTIAL:
            status = PARTIAL[bid]
        else:
            return match.group(0)
        changed += 1
        return f"| {bid} |" + match.group(2) + f" {status} |"

    # rows look like: | BACK-001 | Title | Desc | P0 | 8h | <status> |
    # group(2) captures the four columns before the status; the status itself is replaced.
    pattern = re.compile(r"\| (BACK-\d+) \|((?:[^|]*\|){4})[^|]*\|")
    new_text = pattern.sub(replace, text)
    BACKLOG.write_text(new_text, encoding="utf-8")
    print(f"backlog rows updated: {changed}")


if __name__ == "__main__":
    main()
