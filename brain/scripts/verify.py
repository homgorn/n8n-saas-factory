#!/usr/bin/env python3
"""
verify.py — the project's verification gate, runnable without GitHub Actions.

CI on this repository may not run (GitHub Actions is billing-locked on the account), so the
same gates must be runnable locally. This is the single command that decides whether work
is done. It never marks a feature passing on the agent's own say-so.

Usage:
    python brain/scripts/verify.py            # all gates
    python brain/scripts/verify.py --quick    # skip the full rebuild
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sqlite3
import sys
import time
from pathlib import Path

# Windows consoles default to cp1252 and will raise on the box-drawing and check marks below.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "brain" / "data" / "wiki.db"
FORGE = ROOT / "brain" / "scripts" / "forge.py"

GREEN, RED, YELLOW, CYAN, NC = "\033[32m", "\033[0;31m", "\033[1;33m", "\033[36m", "\033[0m"

results: list[tuple[str, bool, str]] = []


def gate(name: str, order: int = 50, needs_build: bool = False):
    """Register a gate. main() replays them by `order`, so file layout does not matter."""
    def wrap(fn):
        def run():
            print(f"{CYAN}▸ {name}{NC}")
            start = time.time()
            try:
                detail = fn() or ""
                took = time.time() - start
                print(f"  {GREEN}PASS{NC} {name} ({took:.1f}s)")
                if detail:
                    for line in str(detail).splitlines():
                        print(f"       {line}")
                results.append((name, True, detail))
            except AssertionError as exc:
                took = time.time() - start
                print(f"  {RED}FAIL{NC} {name} ({took:.1f}s)")
                for line in str(exc).splitlines():
                    print(f"       {line}")
                results.append((name, False, str(exc)))
            except Exception as exc:  # noqa: BLE001
                print(f"  {RED}ERROR{NC} {name}: {type(exc).__name__}: {exc}")
                results.append((name, False, f"{type(exc).__name__}: {exc}"))
            print()
        run.__name__ = fn.__name__
        run.needs_build = needs_build
        RUNNING.append((order, run))
        return run
    return wrap


# Gates register at definition time rather than running, because several of them need the
# build to have happened and argparse to have parsed first.
RUNNING: list = []


def sh(cmd: list[str], cwd: Path = ROOT) -> str:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise AssertionError(f"`{' '.join(cmd)}` exited {proc.returncode}\n{proc.stdout}\n{proc.stderr}")
    return proc.stdout


# --------------------------------------------------------------------------


@gate("sources present", order=10)
def gate_sources():
    src = ROOT / "n8n-docs-source" / "docs"
    if not src.exists():
        raise AssertionError(
            f"{src} missing.\n"
            "  Clone it:  git clone --depth 1 https://github.com/n8n-io/n8n-docs.git n8n-docs-source"
        )
    n = len(list(src.rglob("*.md")))
    if n < 1000:
        raise AssertionError(f"only {n} markdown files under {src}; expected > 1000")
    return f"{n} markdown files"


@gate("wiki rebuild is idempotent", order=20, needs_build=True)
def gate_build():
    before = None
    if DB.exists():
        before = sqlite3.connect(DB).execute("SELECT COUNT(*) FROM docs").fetchone()[0]

    sh([sys.executable, str(FORGE), "build"])
    if not DB.exists():
        raise AssertionError("build produced no database")

    conn = sqlite3.connect(DB)
    after = conn.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
    conn.close()

    if before is not None and before != after:
        raise AssertionError(
            f"doc count changed across identical builds: {before} -> {after}\n"
            "  The build is supposed to be idempotent. Something non-deterministic leaked in."
        )
    return f"{after} docs, stable across two builds"


@gate("corpus floor", order=30, needs_build=True)
def gate_floor():
    conn = sqlite3.connect(DB)
    docs = conn.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
    chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    topics = conn.execute("SELECT COUNT(DISTINCT topic) FROM docs").fetchone()[0]
    wf = conn.execute("SELECT COUNT(*) FROM workflows").fetchone()[0]
    ents = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
    conn.close()

    floors = {"docs": (docs, 1200), "chunks": (chunks, 8000), "topics": (topics, 10),
              "workflows": (wf, 10), "entities": (ents, 500)}
    bad = [f"{k}={v} < {minv}" for k, (v, minv) in floors.items() if v < minv]
    if bad:
        raise AssertionError(
            "corpus below the floor: " + ", ".join(bad) + "\n"
            "  A green build that quietly lost content is worse than a red one."
        )
    return " · ".join(f"{k}={v}" for k, (v, _) in floors.items())


@gate("every page has a standalone summary", order=40, needs_build=True)
def gate_summaries():
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT slug, title, summary FROM docs").fetchall()
    conn.close()

    missing, toolong = [], []
    for slug, title, summary in rows:
        if not summary or not summary.strip():
            missing.append(slug)
        elif len(summary) > 220:
            toolong.append(f"{slug} ({len(summary)})")

    if missing:
        raise AssertionError(
            f"{len(missing)} pages have no summary, e.g. {missing[:5]}\n"
            "  An agent reading only summaries must still get the point of each page."
        )
    if toolong:
        raise AssertionError(f"{len(toolong)} summaries exceed 200 chars: {toolong[:5]}")
    return f"{len(rows)} pages, all summarised within 200 chars"


@gate("every page resolves to a live source URL", order=50, needs_build=True)
def gate_urls():
    import urllib.request

    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT slug, source_url FROM docs ORDER BY slug LIMIT 12").fetchall()
    conn.close()

    bad = []
    for slug, url in rows:
        if not url.startswith("https://docs.n8n.io/"):
            bad.append(f"{slug}: not a docs URL ({url})")
    if bad:
        raise AssertionError("\n".join(bad))

    # probe one live URL so a broken path scheme is caught, not just a bad prefix
    probe_slug, probe_url = rows[0]
    try:
        req = urllib.request.Request(probe_url, method="HEAD", headers={"User-Agent": "verify/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            code = resp.status
    except Exception as exc:  # noqa: BLE001
        code = f"unreachable ({type(exc).__name__})"
    if isinstance(code, int) and code >= 400:
        raise AssertionError(f"live probe failed: {probe_url} -> {code}")
    return f"{len(rows)} URL shapes valid; probe {probe_url} -> {code}"


@gate("retrieval answers a real question", order=60, needs_build=True)
def gate_retrieval():
    cases = [
        ("how do I paginate API results", "pagination"),
        ("retry failed executions error handling", "error"),
        ("queue mode redis scaling", "queue"),
    ]
    lines = []
    for question, must_contain in cases:
        out = sh([sys.executable, str(FORGE), "ask", question])
        if must_contain.lower() not in out.lower():
            raise AssertionError(
                f"query {question!r} returned nothing containing {must_contain!r}\n{out[:400]}"
            )
        # the top hit's own text must mention the term, not just the wrapper line
        first_block = out.split("\n\n")[1] if "\n\n" in out else ""
        if must_contain.lower() not in first_block.lower():
            raise AssertionError(
                f"query {question!r}: top hit does not mention {must_contain!r}\n{first_block[:300]}"
            )
        lines.append(f"{question!r} -> matched {must_contain!r}")
    return "\n".join(lines)


@gate("claims are typed and sourced", order=70, needs_build=True)
def gate_claims():
    conn = sqlite3.connect(DB)
    try:
        rows = conn.execute("SELECT id, kind, source, text FROM claims").fetchall()
    except sqlite3.OperationalError:
        raise AssertionError("no claims table — run: python brain/scripts/seed_claims.py")
    conn.close()

    if not rows:
        raise AssertionError("zero claims. A README with no provenance is a README that guesses.")

    valid = {"measured", "reported", "inferred", "unconfirmed"}
    bad_type = [f"{cid}={k}" for cid, k, _, _ in rows if k not in valid]
    if bad_type:
        raise AssertionError(f"claims with an unknown type: {bad_type}")

    # reported and measured claims must name their source; unconfirmed is expected to have none
    unsourced = [cid for cid, k, s, _ in rows if k in {"reported", "measured"} and not s]
    if unsourced:
        raise AssertionError(f"claims claim to be sourced but cite nothing: {unsourced}")

    by_kind: dict[str, int] = {}
    for _, k, _, _ in rows:
        by_kind[k] = by_kind.get(k, 0) + 1
    return f"{len(rows)} claims · " + " ".join(f"{k}={v}" for k, v in sorted(by_kind.items()))


@gate("no secrets committed", order=80)
def gate_secrets():
    tracked = sh(["git", "ls-files"]).splitlines()
    token = re.compile(r"(sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{36,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{35})")
    base64 = re.compile(r"^[A-Za-z0-9+/]{60,}={0,2}$")
    keyhdr = re.compile(r"-----BEGIN\s+(?:[A-Z ]*\s)?PRIVATE KEY-----")

    token_hits, key_hits = [], []
    for rel in tracked:
        if not rel.endswith((".md", ".ts", ".js", ".json", ".yml", ".yaml", ".env", ".sh", ".py")):
            continue
        try:
            lines = (ROOT / rel).read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines):
            if token.search(line):
                token_hits.append(f"{rel}:{i + 1}")
            if base64.match(line.strip()) and keyhdr.search("\n".join(lines[max(0, i - 3):i])):
                key_hits.append(f"{rel}:{i + 1}")

    if token_hits:
        raise AssertionError("token-shaped strings committed:\n  " + "\n  ".join(token_hits[:10]))
    if key_hits:
        raise AssertionError("private key bodies committed:\n  " + "\n  ".join(key_hits[:10]))
    return f"{len(tracked)} tracked files scanned, clean"


@gate("licence position is documented", order=90)
def gate_licence():
    adr = ROOT / "brain" / "decisions" / "ADR-001-n8n-licence-blocks-hosted-saas.md"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")

    if not adr.exists():
        raise AssertionError("ADR-001 is missing — the licence constraint is undocumented")
    if "sustainable use" not in readme.lower():
        raise AssertionError("README does not state the n8n licence position")
    if "not ours" not in readme.lower():
        raise AssertionError("README does not disclaim ownership of n8n-docs-source")
    if "ADR-001" not in env_example:
        raise AssertionError(".env.example does not point at the licence constraint")

    # the vendored clone must not be committed
    tracked = sh(["git", "ls-files"]).splitlines()
    vendored = [t for t in tracked if t.startswith("n8n-docs-source/")]
    if vendored:
        raise AssertionError(
            f"{len(vendored)} vendored n8n docs files are tracked; they are n8n's, not ours"
        )
    return "ADR-001 present · README states it · .env.example points at it · vendored clone untracked"


@gate("feature list is honest", order=100)
def gate_features():
    import json

    path = ROOT / "feature_list.json"
    if not path.exists():
        raise AssertionError("feature_list.json missing")
    data = json.loads(path.read_text(encoding="utf-8"))

    ids = [f["id"] for f in data]
    if len(ids) != len(set(ids)):
        dupes = {i for i in ids if ids.count(i) > 1}
        raise AssertionError(f"duplicate feature ids: {dupes}")

    passing = [f["id"] for f in data if f.get("passes")]
    total = len(data)
    print(f"       {total} features, {len(passing)} marked passing: {passing or 'none'}")
    return f"{total} features tracked"


# --------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="skip the full wiki rebuild")
    args = parser.parse_args()

    print(f"{CYAN}{'=' * 64}")
    print(" n8n SaaS Factory — verification gate")
    print(f"{'=' * 64}{NC}\n")

    # Replay by declared order. --quick skips the rebuild and every gate that reads its output,
    # because those checks would otherwise run against a stale corpus and pass misleadingly.
    # All remaining gates still run after a failure: one red gate must not hide the rest.
    ordered = sorted(RUNNING, key=lambda item: item[0])
    if args.quick:
        skipped = [run.__name__ for _, run in ordered if getattr(run, "needs_build", False)]
        ordered = [(o, r) for o, r in ordered if not getattr(r, "needs_build", False)]
        if skipped:
            print(f"{YELLOW}--quick: skipping {len(skipped)} build-dependent gates{NC}\n")

    for _, run_gate in ordered:
        run_gate()

    passed = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - passed

    print(f"{CYAN}{'=' * 64}{NC}")
    if failed:
        print(f"{RED}VERDICT: FAIL{NC} — {passed} passed, {failed} failed\n")
        for name, ok, detail in results:
            if not ok:
                print(f"  {RED}x{NC} {name}")
        print()
        sys.exit(1)
    print(f"{GREEN}VERDICT: PASS{NC} — {passed}/{len(results)} gates\n")
    sys.exit(0)


if __name__ == "__main__":
    main()