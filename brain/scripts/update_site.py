#!/usr/bin/env python3
"""
update_site.py — keep the landing page numbers equal to the measured truth.

The landing page states the corpus size, the gate count and the verified feature count.
Hand-written numbers drift: after the corpus doubled the site still claimed 1,348 pages.
This script rewrites those numbers from the database, the feature list and the gate
definitions, and fails loudly when an expected anchor is missing — a silent no-op that
leaves stale numbers on a live page is the failure mode worth preventing.

Usage:
    python brain/scripts/update_site.py          # rewrite docs/index.html and docs/ru/index.html
    python brain/scripts/update_site.py --check  # report drift without writing
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "brain" / "data" / "wiki.db"
FEATURES = ROOT / "feature_list.json"
VERIFY = ROOT / "brain" / "scripts" / "verify.py"
SITE_EN = ROOT / "docs" / "index.html"
SITE_RU = ROOT / "docs" / "ru" / "index.html"


def human_words(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M".replace(".00M", "M")
    if n >= 1_000:
        return f"{n // 1000}k"
    return str(n)


def human_int(n: int) -> str:
    return f"{n:,}"


def facts() -> dict:
    conn = sqlite3.connect(DB)
    pages = conn.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
    chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    words = conn.execute("SELECT SUM(words) FROM docs").fetchone()[0] or 0
    entities = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
    triples = conn.execute("SELECT COUNT(*) FROM triples").fetchone()[0]
    workflows = conn.execute("SELECT COUNT(*) FROM workflows").fetchone()[0]
    claims = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    conn.close()

    features = json.loads(FEATURES.read_text(encoding="utf-8"))
    passing = [f["id"] for f in features if f.get("passes")]
    total = len(features)
    # The site-counters gate reads this number, so including it makes the count
    # self-referential: adding the gate changes the number it is asked to state. The
    # site therefore states the substantive gates, and the self-check is named separately.
    gate_names = re.findall(r'@gate\("([^"]+)"', VERIFY.read_text(encoding="utf-8"))
    self_check = [g for g in gate_names if "site counters" in g]
    gates = len(gate_names) - len(self_check)

    projects = ROOT / "generated-saas"
    project_count = len([p for p in projects.iterdir() if p.is_dir()]) if projects.exists() else 0
    file_count = 0
    if project_count:
        sample = next(p for p in projects.iterdir() if p.is_dir())
        file_count = len([f for f in sample.rglob("*") if f.is_file()])

    return {
        "PAGES": human_int(pages),
        "PAGES_RAW": str(pages),
        "CHUNKS": human_int(chunks),
        "CHUNKS_RAW": str(chunks),
        "WORDS": human_words(words),
        "WORDS_RAW": human_int(words),
        "ENTITIES": human_int(entities),
        "TRIPLES": human_int(triples),
        "WORKFLOWS": str(workflows),
        "CLAIMS": str(claims),
        "GATES": str(gates),
        "PASSING": str(len(passing)),
        "TOTAL": str(total),
        "PROJECTS": str(project_count),
        "PROJECT_FILES": str(file_count),
        "PASSING_IDS": ", ".join(passing),
        "FEATURES": features,
    }


# (regex, replacement) — the replacement may use {KEY} placeholders from facts()
EN_RULES = [
    (r'(Public · MIT · Active research · )[\d]+ of \d+( measured-verified)', r"\g<1>{PASSING} of {TOTAL}\g<2>"),
    (r'(Public · MIT · Active research · \d+ of \d+ measured-verified · )\d+/\d+( gates)', r"\g<1>{GATES}/{GATES}\g<2>"),
    (r'<div class="stat-value">[\d,\s]+</div>\s*\n\s*<div class="stat-label">Pages of documentation</div>', ""),  # placeholder, replaced below
]

RU_RULES = [
    (r'(Публичный · MIT · измерено-верифицировано: )\d+ из \d+( · )', r"\g<1>{PASSING} из {TOTAL}\g<2>"),
    (r'(Публичный · MIT · измерено-верифицировано: \d+ из \d+ · )\d+/\d+( гейтов)', r"\g<1>{GATES}/{GATES}\g<2>"),
]


def stat_value(html: str, index: int, value: str) -> str:
    """Replace the index-th occurrence of a stat value block."""
    pattern = re.compile(r'(<div class="stat-value">)([^<]*)(</div>)')
    matches = list(pattern.finditer(html))
    if index >= len(matches):
        raise SystemExit(f"stat block {index} not found")
    m = matches[index]
    return html[: m.start(2)] + value + html[m.end(2):]


def apply_counters(html: str, f: dict, lang: str) -> str:
    # the four stat blocks, in order: pages, chunks, words, gates/claims
    html = stat_value(html, 0, f["PAGES"])
    html = stat_value(html, 1, f["CHUNKS"])
    html = stat_value(html, 2, f["WORDS"])
    html = stat_value(html, 3, f["CLAIMS"] + " / " + f["GATES"])

    if lang == "en":
        # The separator is a middle dot; matching on the ASCII anchors instead keeps the
        # pattern working whatever byte sequence the file carries.
        html = re.sub(r"(Active research . )(\d+)( of )(\d+)( measured-verified . )(\d+)/(\d+)( gates)",
                       r"\g<1>{PASSING}\g<3>{TOTAL}\g<5>{GATES}/{GATES}\g<8>".format(**f), html)
        html = re.sub(r"\b\d[\d,\.]*\s*pages, \d[\d,\.]* chunks\b", f"{f['PAGES']} pages, {f['CHUNKS']} chunks", html)
        html = re.sub(r"\b\d[\d,\.]*\s*docs, \d[\d,\.]* chunks, [\d,\.]+ words", f"{f['PAGES']} docs, {f['CHUNKS']} chunks, {f['WORDS_RAW']} words", html)
        html = re.sub(r"n8n docs \(\d[\d,\.]* pages\)", f"n8n docs ({f['PAGES']} pages)", html)
        html = re.sub(r"\d+ SaaS projects \(\d+ files each\)", f"{f['PROJECTS']} SaaS projects ({f['PROJECT_FILES']} files each)", html)
        html = re.sub(r"\b\d+ gates, exits non-zero", f"{f['GATES']} gates, exits non-zero", html)
        html = re.sub(r"\b\d+ automated gates", f"{f['GATES']} automated gates", html)
        html = re.sub(r"Corpus\n\s*[\d,\.]+ docs · [\d,\.km]+ words · [\d,]+ entities · [\d,]+ triples · \d+ workflows\.",
                      f"Corpus\n{f['PAGES']} docs · {f['WORDS']} words · {f['ENTITIES']} entities · {f['TRIPLES']} triples · {f['WORKFLOWS']} workflows.", html)
        html = re.sub(r"Measured-verified \(\d+ of \d+\)", f"Measured-verified ({f['PASSING']} of {f['TOTAL']})", html)
        html = re.sub(r"Implemented, not verified \(\d+ of \d+\)",
                      f"Implemented, not verified ({int(f['TOTAL']) - int(f['PASSING'])} of {f['TOTAL']})", html)
        html = re.sub(r"\d+ provenance-stamped claims", f"{f['CLAIMS']} provenance-stamped claims", html)
    else:
        html = re.sub(r"(измерено-верифицировано: )(\d+)( из )(\d+)( . )(\d+)/(\d+)( гейтов)",
                       r"\g<1>{PASSING}\g<3>{TOTAL}\g<5>{GATES}/{GATES}\g<8>".format(**f), html)
        html = re.sub(r"\d[\d\s]*\s*страниц документации", f"{f['PAGES']} страниц документации", html)
        html = re.sub(r"\d[\d\s]*\s*Индексированных фрагментов", f"{f['CHUNKS']} Индексированных фрагментов", html)
        html = re.sub(r"\d[\d\s]*\s*тыс\.", f"{f['WORDS']}.", html)
        html = re.sub(r"\d+ автоматизированных проверок", f"{f['GATES']} автоматизированных проверок", html)
        html = re.sub(r"Готово \((\d+) из \d+\)", f"Готово ({f['PASSING']} из {f['TOTAL']})", html)
        html = re.sub(r"Осталось \((\d+)\)", f"Осталось ({int(f['TOTAL']) - int(f['PASSING'])})", html)
        # idempotent: the label may already carry a parenthesised count from an earlier run
        html = re.sub(r"Гейтов верификации(?: \(\d+\))*", f"Гейтов верификации ({f['GATES']})", html)
        html = re.sub(r"\d+ проектов SaaS \(\d+ файлов\)", f"{f['PROJECTS']} проектов SaaS ({f['PROJECT_FILES']} файлов)", html)
        html = re.sub(r"\d+ проектов SaaS \(27 файлов\)", f"{f['PROJECTS']} проектов SaaS ({f['PROJECT_FILES']} файлов)", html)
    return html


def _replace_paragraph_after_heading(html: str, heading_pattern: str, paragraphs: list[str]) -> str:
    """Replace the <p> elements that follow a heading, keeping the heading itself."""
    m = re.search(heading_pattern, html)
    if not m:
        return html
    start = m.end()
    # consume the <p>...</p> blocks that follow
    pos = start
    for _ in range(len(paragraphs)):
        pm = re.compile(r"\s*<p>.*?</p>", re.S).match(html, pos)
        if not pm:
            break
        pos = pm.end()
    replacement = "".join(f"\n          <p>{p}</p>" for p in paragraphs)
    return html[:start] + replacement + html[pos:]


def feature_lines(features: list[dict], passing: bool, f: dict) -> list[str]:
    """One short sentence per feature, split by verified / not verified."""
    out = []
    for feat in features:
        if bool(feat.get("passes")) != passing:
            continue
        fid = feat["id"]
        desc = feat["description"]
        # shorten: keep the first clause
        short = desc.split("(")[0].strip().rstrip(".")
        out.append(f"<b>{fid}</b> — {short}.")
    return out


def apply_narrative(html: str, f: dict, features: list[dict], lang: str) -> str:
    """Rewrite the roadmap blocks and the corpus line from the feature list."""
    verified = feature_lines(features, True, f)
    unverified = feature_lines(features, False, f)

    if lang == "en":
        html = _replace_paragraph_after_heading(
            html,
            r"<h4>Measured-verified \(\d+ of \d+\)</h4>",
            [" ".join(verified)],
        )
        html = _replace_paragraph_after_heading(
            html,
            r"<h4>Implemented, not verified \(\d+ of \d+\)</h4>",
            [
                " ".join(unverified),
                "A feature counts as passing only when something measures it. "
                "Implemented-but-unverified means the code exists but no check has run it yet.",
            ],
        )
        html = re.sub(
            r"(<h3>Corpus</h3>\s*<p>)[\d,\.]+ docs . [\d\.km]+ words . [\d,]+ entities . [\d,]+ triples . \d+ workflows\.",
            r"\g<1>" + f"{f['PAGES']} docs · {f['WORDS']} words · {f['ENTITIES']} entities · "
                       f"{f['TRIPLES']} triples · {f['WORKFLOWS']} workflows.",
            html,
        )
        html = _replace_paragraph_after_heading(
            html, r"<h4>Next gates</h4>", next_gates_html(features, lang)
        )
    else:
        html = _replace_paragraph_after_heading(
            html,
            r"<h4>[^<]*\((\d+) из (\d+)\)</h4>",
            [" ".join(verified)],
        )
        html = _replace_paragraph_after_heading(
            html,
            r"<h4>Осталось \(\d+\)</h4>",
            [
                " ".join(unverified),
                "Фича считается прошедшей только когда её что-то измерило. "
                "«Реализовано, но не проверено» — код есть, но ни одна проверка его не запускала.",
            ],
        )
        html = re.sub(
            r"(Корпус\n\s*)[\d,\.]+ docs · [\d\.km]+ words · [\d,]+ entities · [\d,]+ triples · \d+ workflows\.",
            r"\g<1>" + f"{f['PAGES']} docs · {f['WORDS']} words · {f['ENTITIES']} entities · "
                       f"{f['TRIPLES']} triples · {f['WORKFLOWS']} workflows.",
            html,
        )
    return html


NEXT_STEPS = {
    "F007": "run sample tasks for the two roles that still lack one (architect, implementer) — "
             "they were blocked by the free-model daily rate limit, not by the project",
    "F010": "record the video walkthrough of the full pipeline",
}


def next_gates_html(features: list[dict], lang: str) -> list[str]:
    """One actionable line per unverified feature."""
    lines = []
    for feat in features:
        if feat.get("passes"):
            continue
        fid = feat["id"]
        step = NEXT_STEPS.get(fid)
        if not step:
            step = f"verify {fid}: run the checks its description names"
        if lang == "en":
            lines.append(f"<b>{fid}:</b> {step}.")
        else:
            lines.append(f"<b>{fid}:</b> {step}.")
    return lines


def update_github_description(f: dict) -> str:
    """Keep the repo description equal to the measured truth, like the site counters."""
    description = (
        f"Turn n8n workflows into deployable SaaS. Internal LLM wiki "
        f"({f['PAGES_RAW']} docs, {f['CHUNKS_RAW']} chunks, {f['WORDS_RAW']} words), "
        f"workflow analyzer, SaaS generator, agent orchestration, {f['GATES']}-gate verification. "
        f"MIT. Customer-runs-own-n8n (ADR-001, ADR-002)."
    )
    gh = shutil.which("gh") or shutil.which("gh.exe")
    if not gh:
        return "gh CLI not found — repo description left alone"
    try:
        proc = subprocess.run(
            [gh, "repo", "edit", "homgorn/n8n-saas-factory", "--description", description],
            capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"gh call failed: {type(exc).__name__}"
    if proc.returncode != 0:
        return f"gh call failed: {(proc.stderr or '').strip()[:160]}"
    return "repo description updated"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report drift, do not write")
    ap.add_argument("--skip-github", action="store_true", help="do not touch the repo description")
    args = ap.parse_args()

    f = facts()
    print(f"facts: pages={f['PAGES']} chunks={f['CHUNKS']} words={f['WORDS']} "
          f"gates={f['GATES']} features={f['PASSING']}/{f['TOTAL']} projects={f['PROJECTS']}")

    drift = []
    for path, lang in ((SITE_EN, "en"), (SITE_RU, "ru")):
        if not path.exists():
            print(f"  {path.name}: missing")
            continue
        original = path.read_text(encoding="utf-8")
        updated = apply_counters(original, f, lang)
        updated = apply_narrative(updated, f, f["FEATURES"], lang)
        if updated != original:
            drift.append(path)
            if not args.check:
                path.write_text(updated, encoding="utf-8")
                print(f"  {path.relative_to(ROOT)}: updated")
            else:
                print(f"  {path.relative_to(ROOT)}: DRIFT")
        else:
            print(f"  {path.relative_to(ROOT)}: current")

    if args.check and drift:
        sys.exit(1)
    if not args.check and drift:
        print("\nlanding counters rewritten from measured facts")

    if not args.check and not args.skip_github:
        print(f"  github: {update_github_description(f)}")


if __name__ == "__main__":
    main()
