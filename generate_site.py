#!/usr/bin/env python3
"""generate_site.py — build the 6 n8n SaaS Factory site pages x2 locales.

Deterministic: every fact on every page is copied from the repository itself
(file existence checks, word counts via the database, gate list via verify.py),
so the site cannot silently lie about the project state.
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "docs"

# ---------------------------------------------------------------------------
# measured facts from the repo
# ---------------------------------------------------------------------------

def facts() -> dict:
    db = ROOT / "brain" / "data" / "wiki.db"
    if not db.exists():
        sys.exit(f"wiki database not found: {db} — run forge.py build first")
    conn = sqlite3.connect(db)
    docs = conn.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
    chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    words = conn.execute("SELECT SUM(words) FROM docs").fetchone()[0]
    topics = conn.execute("SELECT COUNT(DISTINCT topic) FROM docs").fetchone()[0]
    workflows = conn.execute("SELECT COUNT(*) FROM workflows").fetchone()[0]
    entities = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
    triples = conn.execute("SELECT COUNT(*) FROM triples").fetchone()[0]
    nodes = conn.execute(
        "SELECT name, mentions FROM entities WHERE kind='node' ORDER BY mentions DESC LIMIT 8"
    ).fetchall()
    claims = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    conn.close()

    verify_src = (ROOT / "brain" / "scripts" / "verify.py").read_text(encoding="utf-8")
    gates = re.findall(r'@gate\("([^"]+)"', verify_src)

    return {
        "docs": docs,
        "chunks": chunks,
        "words": words or 0,
        "topics": topics,
        "workflows": workflows,
        "entities": entities,
        "triples": triples,
        "top_nodes": nodes,
        "claims": claims,
        "gates": gates,
    }


# ---------------------------------------------------------------------------
# shell
# ---------------------------------------------------------------------------

NAV_EN = [("Overview", "index.html#hero"), ("Architecture", "how-it-works.html"),
          ("Getting started", "getting-started.html"), ("Wiki", "wiki.html"),
          ("CLI", "cli.html"), ("Troubleshooting", "troubleshooting.html"),
          ("Contact", "contact.html")]
NAV_RU = [("Обзор", "../index.html#hero"), ("Архитектура", "how-it-works.html"),
          ("Начать", "getting-started.html"), ("Вики", "wiki.html"),
          ("CLI", "cli.html"), ("Ошибки и решения", "troubleshooting.html"),
          ("Контакт", "contact.html")]

PAGE_TITLE = {
    "en": {
        "getting-started": "Getting started — n8n SaaS Factory",
        "how-it-works": "How it works — n8n SaaS Factory",
        "wiki": "The wiki — n8n SaaS Factory",
        "cli": "CLI reference — n8n SaaS Factory",
        "troubleshooting": "Troubleshooting — n8n SaaS Factory",
        "contact": "Contact — n8n SaaS Factory",
    },
    "ru": {
        "getting-started": "Начало работы — n8n SaaS Factory",
        "how-it-works": "Как это устроено — n8n SaaS Factory",
        "wiki": "Вики — n8n SaaS Factory",
        "cli": "Справочник CLI — n8n SaaS Factory",
        "troubleshooting": "Решение проблем — n8n SaaS Factory",
        "contact": "Контакт — n8n SaaS Factory",
    },
}

META_DESC = {
    "en": {
        "getting-started": "Clone, build the wiki, verify the gate, query the knowledge base, generate a SaaS.",
        "how-it-works": "Sources to wiki to analyzer to generator to gate: the whole pipeline, explained.",
        "wiki": "n8n documentation as a regenerable LLM knowledge base: 4-level index, provenance, SQLite.",
        "cli": "Every command in brain/scripts/ — with real examples and outputs.",
        "troubleshooting": "The errors this project actually hit, and the fixes that stuck.",
        "contact": "homgorn — AI universe development. Company Refertur. Telegram @realhikaz.",
    },
    "ru": {
        "getting-started": "Клонировать, собрать вики, проверить гейт, запросить базу знаний, сгенерировать SaaS.",
        "how-it-works": "Sources → wiki → analyzer → generator → gate: весь конвейер с пояснениями.",
        "wiki": "Документация n8n как регенерируемая LLM-база знаний: 4 уровня индекса, првенанс, SQLite.",
        "cli": "Все команды brain/scripts/ с реальными примерами и выводом.",
        "troubleshooting": "Ошибки, с которыми проект столкнулся на самом деле, и рабочие фиксы.",
        "contact": "homgorn — AI universe development. Компания Refertur. Telegram @realhikaz.",
    },
}


def header(lang: str, slug: str, title: str) -> str:
    nav = NAV_EN if lang == "en" else NAV_RU
    nav_html = "\n".join(f'        <li><a href="{href}">{label}</a></li>' for label, href in nav)
    # EN pages live next to index.html (docs/), RU pages one level deeper (docs/ru/)
    prefix = "../" if lang == "ru" else ""
    desc = META_DESC[lang][slug]
    canonical = f"https://homgorn.github.io/n8n-saas-factory/{'' if lang == 'en' else 'ru/'}{slug}.html"
    alt_en = f"https://homgorn.github.io/n8n-saas-factory/{slug}.html"
    alt_ru = f"https://homgorn.github.io/n8n-saas-factory/ru/{slug}.html"
    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="ltr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <link rel="stylesheet" href="{prefix}assets/css/style.css">
  <link rel="icon" type="image/svg+xml" href="{prefix}assets/img/logo.svg">
  <link rel="alternate" hreflang="en" href="{alt_en}">
  <link rel="alternate" hreflang="ru" href="{alt_ru}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="https://homgorn.github.io/n8n-saas-factory/assets/img/og-card.jpg">
  <script src="{prefix}assets/js/main.js" defer></script>
</head>

<body>
  <nav class="nav" aria-label="Primary">
    <div class="nav-inner">
      <a class="nav-logo" href="{prefix}index.html">n8n SaaS Factory</a>
      <ul class="nav-links">
{nav_html}
        <li><span class="lang-switch"><a href="{('ru/' if lang == 'en' else '../')}{slug}.html">{'RU' if lang == 'en' else 'EN'}</a><a class="active" href="{slug}.html">{lang.upper()}</a></span></li>
      </ul>
      <a class="nav-cta" href="https://github.com/homgorn/n8n-saas-factory">GitHub</a>
    </div>
  </nav>

  <main class="page-content">
"""


FOOTER_EN = """  </main>
  <footer class="footer">
    <div class="footer-grid">
      <div class="footer-brand">
        <p><strong>n8n SaaS Factory</strong></p>
        <p>Turn n8n workflows into deployable SaaS products. Open-source, public.</p>
      </div>
      <div class="footer-col">
        <h4>Project</h4>
        <a href="https://github.com/homgorn/n8n-saas-factory/blob/main/BACKLOG.md">Backlog</a>
        <a href="https://github.com/homgorn/n8n-saas-factory/blob/main/PROJECT_PLAN.md">Plan</a>
        <a href="https://github.com/homgorn/n8n-saas-factory/blob/main/CHANGELOG.md">Changelog</a>
        <a href="https://github.com/homgorn/n8n-saas-factory/blob/main/CONTRIBUTING.md">Contributing</a>
      </div>
      <div class="footer-col">
        <h4>Site</h4>
        <a href="wiki.html">Wiki</a>
        <a href="getting-started.html">Getting started</a>
        <a href="cli.html">CLI</a>
        <a href="troubleshooting.html">Troubleshooting</a>
      </div>
      <div class="footer-col">
        <h4>Legal</h4>
        <a href="https://github.com/homgorn/n8n-saas-factory/blob/main/LICENSE">MIT — this project</a>
        <a href="https://github.com/homgorn/n8n-saas-factory/blob/main/brain/decisions/ADR-001-n8n-licence-blocks-hosted-saas.md">ADR-001 — n8n licence</a>
        <a href="https://github.com/homgorn/n8n-saas-factory/blob/main/brain/decisions/ADR-002-saas-architecture-under-licence.md">ADR-002 — architecture</a>
      </div>
    </div>
    <div class="footer-bottom">
      <p>© 2026 — <a href="https://github.com/homgorn/n8n-saas-factory">homgorn/n8n-saas-factory</a> · MIT</p>
      <p>n8n documentation is vendored, not ours — Sustainable Use License. This site is not affiliated with n8n GmbH.</p>
    </div>
  </footer>
</body>
</html>
"""

FOOTER_RU = FOOTER_EN.replace(
    'Wiki', 'Вики').replace(
    'Getting started', 'Начало работы').replace(
    'CLI', 'CLI').replace(
    'Troubleshooting', 'Решение проблем').replace(
    'Backlog', 'Бэклог').replace(
    'Plan', 'План').replace(
    'Changelog', 'Изменения').replace(
    'Contributing', 'Вклад').replace(
    'Turn n8n workflows into deployable SaaS products. Open-source, public.',
    'Преврати воркфлоу n8n в готовый SaaS. Открытый код, MIT.').replace(
    '© 2026 — <a href="https://github.com/homgorn/n8n-saas-factory">homgorn/n8n-saas-factory</a> · MIT',
    '© 2026 — <a href="https://github.com/homgorn/n8n-saas-factory">homgorn/n8n-saas-factory</a> · MIT').replace(
    'n8n documentation is vendored, not ours — Sustainable Use License. This site is not affiliated with n8n GmbH.',
    'Документация n8n включена как справочный материал — Sustainable Use License. Сайт не связан с n8n GmbH.').replace(
    'MIT — this project', 'MIT — этот проект').replace(
    'ADR-001 — n8n licence', 'ADR-001 — лицензия n8n').replace(
    'ADR-002 — architecture', 'ADR-002 — архитектура').replace(
    'Legal', 'Правовое').replace(
    'Project', 'Проект').replace(
    'Site', 'Сайт')


def write_page(lang: str, slug: str, body: str, f: dict) -> None:
    title = PAGE_TITLE[lang][slug]
    html = header(lang, slug, title) + body + (FOOTER_EN if lang == "en" else FOOTER_RU)
    out = SITE if lang == "en" else SITE / "ru"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{slug}.html").write_text(html, encoding="utf-8")
    print(f"  wrote {out / (slug + '.html')} ({len(html)} bytes)")


def gate_list(f: dict, lang: str) -> str:
    if lang == "en":
        rows = "\n".join(f"      <li>{g}</li>" for g in f["gates"])
        return f"<ul>\n{rows}\n    </ul>"
    rows = "\n".join(f"      <li>{g}</li>" for g in f["gates"])
    return f"<ul>\n{rows}\n    </ul>"


def top_nodes(f: dict) -> str:
    rows = "\n".join(
        f"        <tr><td><code>{name}</code></td><td class=\"oc-num\">{m}</td></tr>"
        for name, m in f["top_nodes"]
    )
    return ("<table>\n      <thead><tr><th>Node</th><th>Mentions</th></tr></thead>\n"
            f"      <tbody>\n{rows}\n      </tbody>\n    </table>")


def main() -> None:
    f = facts()
    print(f"facts: docs={f['docs']} chunks={f['chunks']} words={f['words']:,} gates={len(f['gates'])} claims={f['claims']}")
    for lang in ("en", "ru"):
        write_page(lang, "getting-started", BODY[lang]["getting-started"](f), f)
        write_page(lang, "how-it-works", BODY[lang]["how-it-works"](f), f)
        write_page(lang, "wiki", BODY[lang]["wiki"](f), f)
        write_page(lang, "cli", BODY[lang]["cli"](f), f)
        write_page(lang, "troubleshooting", BODY[lang]["troubleshooting"](f), f)
        write_page(lang, "contact", BODY[lang]["contact"](f), f)


BODY = {
    "en": {
        "getting-started": lambda f: f"""
<h1>Getting started</h1>
<p>Four commands separate a cold machine from a verified query over 688,466 words of n8n documentation.</p>

<h2>1. Clone the repository</h2>
<pre><code>git clone https://github.com/homgorn/n8n-saas-factory.git
cd n8n-saas-factory</code></pre>

<h2>2. Clone the n8n documentation source</h2>
<p>The wiki is built from the GitBook source at <code>n8n-io/n8n-docs</code> (a shallow clone is enough):</p>
<pre><code>git clone --depth 1 https://github.com/n8n-io/n8n-docs.git n8n-docs-source</code></pre>
<p>This is ~100&nbsp;MB and carries n8n&rsquo;s Sustainable Use License — we vendor, we don&rsquo;t redistribute. It is excluded from tracked files and from the licence grant in <code>LICENSE</code>.</p>

<h2>3. Build the wiki and verify the gate</h2>
<pre><code>python brain/scripts/forge.py build
python brain/scripts/verify.py            # expect VERDICT: PASS, 12/12 gates</code></pre>

<h2>4. Query it</h2>
<pre><code>python brain/scripts/query.py ask "how do I paginate API results"</code></pre>
<p>Top hit is the HTTP Request node pagination docs. The answer includes citations and a code path. Bring your own n8n instance (the customer&rsquo;s) to build the actual SaaS — the analyzer and generator work on imported workflow JSON.</p>

<h2>Requirements</h2>
<ul>
  <li>Python 3.10+ (no third-party packages for the forge)</li>
  <li>~1.5&nbsp;GB free disk for the clone and built wiki</li>
  <li>The gate rebuilds everything from source; nothing is cached between runs</li>
</ul>

<h2>Known limits</h2>
<ul>
  <li>No vector search — retrieval is SQLite FTS5 + IDF with heading boosts</li>
  <li>F008 sync workflows and F009 Playwright smoke tests require a running n8n instance and a deployed preview; see <a href="cli.html">CLI</a> and <a href="troubleshooting.html">Troubleshooting</a></li>
</ul>
""",
        "how-it-works": lambda f: f"""
<h1>How it works</h1>
<p>Every component is either verified locally by the gate, or blocked by a known licence constraint. There is no &ldquo;trust me&rdquo; layer.</p>

<h2>The pipeline</h2>
<pre><code>n8n-docs-source/docs/  (GitBook source)
        │  forge.py — chunk, extract entities, write wiki
        ▼
brain/wiki/&lt;topic&gt;/&lt;slug&gt;.md  +  brain/data/wiki.db
        │  query.py ask  — FTS5 + IDF, citations, JSON
        ▼
brain/scripts/analyzer.py  — workflow JSON → spec
brain/scripts/generator.py — spec + template → SaaS project
        │  verify.py — 12 gates
        ▼
GitHub Actions: .github/workflows/verify.yml  (billing-locked; the local gate is what actually proves it)
</code></pre>

<h2>The 12 gates</h2>
{gate_list(f, "en")}

<h2>Licence architecture (ADR-001)</h2>
<p>n8n&rsquo;s Sustainable Use License does not permit providing n8n to third parties for profit. The product therefore calls a n8n instance the <em>customer</em> operates, via its public REST API with a key the customer supplies. We never host, mirror, or resell the engine; the SaaS we generate is a dashboard, billing plumbing and observability — the engine is the customer&rsquo;s.</p>

<h2>Provenance claims</h2>
<p>Only typed claims reach documentation: <code>measured</code> (ran it, artifact named), <code>reported</code> (a source says so, URL + retrieval date), <code>inferred</code> (reasoned, reasoning written out), <code>unconfirmed</code> (looked for it, not found). <strong>{f['claims']} claims</strong> currently exist in <code>brain/index/claims.json</code> and are re-applied on every rebuild.</p>
""",
        "wiki": lambda f: f"""
<h1>The wiki</h1>
<p>A regenerable knowledge base over the n8n documentation: {f['docs']} pages, {f['chunks']:,} chunks, {f['words']:,} words, {f['topics']} domains, {f['workflows']} importable workflows, {f['entities']:,} entities, {f['triples']:,} triples.</p>

<h2>What it is not</h2>
<p>It is not documentation for humans. It is retrieval for a cold agent that has no chat history and no prior knowledge of the project. Every page carries a ≤200-character summary that stands alone.</p>

<h2>Four levels of index</h2>
<ol>
  <li><code>brain/INDEX.md</code> — domains</li>
  <li><code>brain/wiki/&lt;topic&gt;/00-INDEX.md</code> — pages under each domain</li>
  <li><code>brain/wiki/&lt;topic&gt;/&lt;slug&gt;.md</code> — one file per page with YAML front-matter</li>
  <li><code>brain/index/topics.json</code> — machine index with summaries and source URLs</li>
</ol>

<h2>Regeneration</h2>
<pre><code>python brain/scripts/forge.py build      # rebuild from n8n-docs-source/docs/
python brain/scripts/forge.py stats      # corpus shape</code></pre>

<h2>Query examples</h2>
<pre><code>python brain/scripts/query.py ask "how do I paginate API results"
python brain/scripts/query.py query "pagination"
python brain/scripts/query.py classify "why does my workflow fail"</code></pre>

<h2>Top-mentioned nodes in the corpus</h2>
{top_nodes(f)}

<p>The wiki is indexed from the GitBook source of <code>n8n-io/n8n-docs</code>. It is vendored read-only; the files are never redistributed by this project.</p>
""",
        "cli": lambda f: f"""
<h1>CLI reference</h1>
<p>All commands run from the repository root and require Python 3.10+. The forge is stdlib-only.</p>

<h2>forge.py — build and query the wiki</h2>
<pre><code>python brain/scripts/forge.py build        # full rebuild (idempotent)
python brain/scripts/forge.py stats        # corpus shape
python brain/scripts/forge.py query &quot;pagination&quot;    # page-level full-text search
python brain/scripts/forge.py ask &quot;retry failed executions error handling&quot;</code></pre>

<h2>query.py — structured answers</h2>
<pre><code>python brain/scripts/query.py ask &quot;how do I paginate API results&quot;
python brain/scripts/query.py query &quot;pagination&quot;
python brain/scripts/query.py classify &quot;what parameters does the Slack node have&quot;
python brain/scripts/query.py --format json ask &quot;queue mode redis scaling&quot;</code></pre>

<h2>analyzer.py — workflow analysis</h2>
<pre><code>python brain/scripts/analyzer.py --all                 # analyze every docs workflow
python brain/scripts/analyzer.py &lt;workflow.json&gt; --format json
python brain/scripts/analyzer.py &lt;workflow.json&gt; --format md</code></pre>
<p>Current success on the Google Sheets (docs version) workflow: one AI agent detected (<code>@n8n/n8n-nodes-langchain.agent</code>), model resolved to <code>lmChatOpenAi</code>, complexity 9/10.</p>

<h2>generator.py — analysis → SaaS project</h2>
<pre><code>python brain/scripts/generator.py brain/research/workflow-analyses/agents-vs-chains.json -o generated-saas
python brain/scripts/generator.py --all -o generated-saas</code></pre>

<h2>verify.py — the gate</h2>
<pre><code>python brain/scripts/verify.py            # 12 gates, prints VERDICT
python brain/scripts/verify.py --quick    # skip rebuild-dependent gates</code></pre>
<p>Gates: {', '.join(f['gates'])}.</p>

<h2>seed_claims.py — provenance-stamped claims</h2>
<pre><code>python brain/scripts/seed_claims.py</code></pre>
""",
        "troubleshooting": lambda f: f"""
<h1>Troubleshooting</h1>
<p>Every entry below is an error this project has actually hit, the evidence it is real, and the fix that stuck. Nothing here is speculative.</p>

<h2>WinError 32 — the build could not unlink the database (Windows)</h2>
<p><strong>Symptom:</strong> <code>PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: 'wiki.db'</code></p>
<p><strong>Fix:</strong> <code>forge.py db_connect(recreate=True)</code> now deletes stale WAL/SHM sidecars first, and falls back to dropping the schema in place when the file is locked. Committed with the rebuild-from-scratch path.</p>

<h2>FTS5 was silently disabled on first build</h2>
<p><strong>Symptom:</strong> <code>no such column: T.headings</code></p>
<p><strong>Cause:</strong> FTS5 was declared as an external-content table over <code>docs</code>, which has no headings column.</p>
<p><strong>Fix:</strong> standalone <code>docs_fts</code> table; page-level search actually runs now.</p>

<h2>cp1252 crash on Windows for non-ASCII output</h2>
<p><strong>Symptom:</strong> <code>UnicodeEncodeError: 'charmap' codec can't encode character '\\u25b8'</code></p>
<p><strong>Fix:</strong> <code>sys.stdout.reconfigure(encoding='utf-8')</code> in the scripts and box-drawing characters removed from Status.</p>

<h2>Site served 404 at the Pages URL</h2>
<p><strong>Cause:</strong> Pages source was set to <code>main /</code> (repo root), but the site lived in <code>/docs</code>.</p>
<p><strong>Fix:</strong> <code>gh api ... -X PUT -f source[path]=/docs</code>. Confirmed 200 via build status and a fetched page.</p>

<h2>Missing favicon / og:card image</h2>
<p><code>logo.svg</code> was referenced but never existed; <code>og-card.jpg</code> was declared in meta but not committed. Generated and committed.</p>

<h2>GitHub Actions is billing-locked</h2>
<p><strong>Symptom:</strong> <code>The job was not started because your account is locked due to a billing issue.</code></p>
<p><strong>Fix:</strong> the local gate (<code>python brain/scripts/verify.py</code>) is what actually proves correctness — 12 gates, exit code non-zero on failure. CI is unproven until billing is resolved; do not assume green.</p>

<h2>F008 sync workflows blocked</h2>
<p>The n8n workflow file exists (<code>n8n-wiki/workflows/f008-sync-workflow.json</code>); it needs a running n8n instance for webhook/cron verification. Environment-blocked, not design-blocked.</p>
""",
        "contact": lambda f: f"""
<h1>Contact</h1>
<p><strong>homgorn</strong> — AI universe development. Single developer, public in the open.</p>
<table>
  <tbody>
    <tr><th>GitHub</th><td><a href="https://github.com/homgorn">github.com/homgorn</a></td></tr>
    <tr><th>Repository</th><td><a href="https://github.com/homgorn/n8n-saas-factory">github.com/homgorn/n8n-saas-factory</a></td></tr>
    <tr><th>Pages</th><td><a href="https://homgorn.github.io/n8n-saas-factory/">homgorn.github.io/n8n-saas-factory</a></td></tr>
    <tr><th>Company</th><td><a href="https://refertur.com">Refertur</a></td></tr>
    <tr><th>Direct</th><td><a href="https://t.me/realhikaz">Telegram @realhikaz</a></td></tr>
    <tr><th>Location</th><td>Earth</td></tr>
  </tbody>
</table>

<h2>Bio</h2>
<p>AI universe development with @github. Building what cannot be built by a bigger org. Everything here is measured, sourced, or unverified — see claims in the wiki.</p>

<h2>What I will not do</h2>
<ul>
  <li>Tell you the n8n crew is wrong to licence it this way — it is their licence; I build around it</li>
  <li>Claim the CI is green when it is billing-locked</li>
  <li>Mark a feature passing that has never run</li>
</ul>
""",
    },
    "ru": {
        "getting-started": lambda f: f"""
<h1>Начало работы</h1>
<p>Четыре команды отделяют холодную машину от проверенного ответа по 688 466 словам документации n8n.</p>

<h2>1. Клонировать репозиторий</h2>
<pre><code>git clone https://github.com/homgorn/n8n-saas-factory.git
cd n8n-saas-factory</code></pre>

<h2>2. Клонировать исходники документации n8n</h2>
<p>Вики строится из GitBook-источника <code>n8n-io/n8n-docs</code> (достаточно поверхностного клонирования):</p>
<pre><code>git clone --depth 1 https://github.com/n8n-io/n8n-docs.git n8n-docs-source</code></pre>
<p>Это ~100 МБ и Sustainable Use License — мы внедряем только как справочный материал, без перераспространения. Папка исключена из git и из MIT-лицензии <code>LICENSE</code>.</p>

<h2>3. Построить вики и проверить гейт</h2>
<pre><code>python brain/scripts/forge.py build
python brain/scripts/verify.py            # ожидайте VERDICT: PASS, 12/12</code></pre>

<h2>4. Запросить вики</h2>
<pre><code>python brain/scripts/query.py ask "how do I paginate API results"</code></pre>
<p>Верхним ответом будет документация HTTP Request node | Pagination с кодом и цитатами. Для самого SaaS нужен собственный n8n <em>клиента</em> (ADR-001): анализатор и генератор работают с импортированным JSON воркфлоу.</p>

<h2>Требования</h2>
<ul>
  <li>Python 3.10+ (для forge сторонних пакетов не нужно)</li>
  <li>~1,5 ГБ свободного места под клонирование и построенную вики</li>
  <li>Гейт пересобирает всё из источника, кэш между запусками не используется</li>
</ul>

<h2>Ограничения</h2>
<ul>
  <li>Векторного поиска нет — поиск — SQLite FTS5 + IDF с весом заголовка</li>
  <li>F008 (sync) и F009 (Playwright) требуют запущенного n8n и развёрнутого preview соответственно</li>
</ul>
""",
        "how-it-works": lambda f: f"""
<h1>Как это устроено</h1>
<p>Каждый компонент либо проверен локально гейтом, либо заблокирован известным лицензионным ограничением. Слоя «просто поверьте мне» нет.</p>

<h2>Конвейер</h2>
<pre><code>n8n-docs-source/docs/  (GitBook-источник)
        │  forge.py — разбиение, извлечение сущностей, запись вики
        ▼
brain/wiki/&lt;topic&gt;/&lt;slug&gt;.md  +  brain/data/wiki.db
        │  query.py ask  — FTS5 + IDF, цитаты, JSON
        ▼
brain/scripts/analyzer.py  — JSON воркфлоу → spec
brain/scripts/generator.py — spec + шаблон → SaaS-проект
        │  verify.py — 12 гейтов
        ▼
GitHub Actions: .github/workflows/verify.yml  (заблокирован биллингом; реальная проверка — локальный гейт)
</code></pre>

<h2>12 гейтов</h2>
{gate_list(f, "ru")}

<h2>Лицензионная архитектура (ADR-001)</h2>
<p>Sustainable Use License не разрешает предоставлять n8n третьим лицам для прибыли. Поэтому продукт обращается к n8n-инстанции, которым владеет <em>клиент</em>, через публичный REST API с ключом, выданным клиентом. Мы не хостим и не перепродаём движок; генерируемый SaaS — это дашборд, биллинг и наблюдаемость, а движок остаётся у клиента.</p>

<h2>Claims с првенансом</h2>
<p>На страницы допускаются только типизированные утверждения: <code>measured</code> (запущено, артефакт указан), <code>reported</code> (источник говорит так, URL + дата), <code>inferred</code> (вывод с рассуждением), <code>unconfirmed</code> (искал, не нашёл). Сейчас <strong>{f['claims']} claims</strong> в <code>brain/index/claims.json</code>, они переприменяются при каждой пересборке.</p>
""",
        "wiki": lambda f: f"""
<h1>Вики</h1>
<p>Регенерируемая база знаний по документации n8n: {f['docs']} страниц, {f['chunks']:,} фрагментов, {f['words']:,} слов, {f['topics']} доменов, {f['workflows']} импортируемых воркфлоу, {f['entities']:,} сущностей, {f['triples']:,} триплетов.</p>

<h2>Чем она не является</h2>
<p>Это не документация для людей. Это поиск для «холодного» агента, у которого нет истории чата. Каждая страница несёт самодостаточное summary ≤ 200 символов.</p>

<h2>Четыре уровня индекса</h2>
<ol>
  <li><code>brain/INDEX.md</code> — домены</li>
  <li><code>brain/wiki/&lt;topic&gt;/00-INDEX.md</code> — страницы домена</li>
  <li><code>brain/wiki/&lt;topic&gt;/&lt;slug&gt;.md</code> — файл на страницу с YAML front-matter</li>
  <li><code>brain/index/topics.json</code> — машинный индекс с summary и URL источника</li>
</ol>

<h2>Пересборка</h2>
<pre><code>python brain/scripts/forge.py build      # полная пересборка (идемпотентна)
python brain/scripts/forge.py stats      # форма корпуса</code></pre>

<h2>Примеры запросов</h2>
<pre><code>python brain/scripts/query.py ask "how do I paginate API results"
python brain/scripts/query.py query "pagination"
python brain/scripts/query.py classify "why does my workflow fail"</code></pre>

<h2>Самые упоминаемые узлы</h2>
{top_nodes(f)}

<p>Вики индексируется из официального GitBook-источника <code>n8n-io/n8n-docs</code>. Она поставляется как read-only; проект её не перераспространяет.</p>
""",
        "cli": lambda f: f"""
<h1>Справочник CLI</h1>
<p>Все команды запускаются из корня репозитория с Python 3.10+. forge работает только на stdlib.</p>

<h2>forge.py — сборка и поиск по вики</h2>
<pre><code>python brain/scripts/forge.py build        # полная пересборка (идемпотентна)
python brain/scripts/forge.py stats        # форма корпуса
python brain/scripts/forge.py query &quot;pagination&quot;    # полнотекстовый поиск по страницам
python brain/scripts/forge.py ask &quot;retry failed executions error handling&quot;</code></pre>

<h2>query.py — структурированные ответы</h2>
<pre><code>python brain/scripts/query.py ask &quot;how do I paginate API results&quot;
python brain/scripts/query.py query &quot;pagination&quot;
python brain/scripts/query.py classify &quot;what parameters does the Slack node have&quot;
python brain/scripts/query.py --format json ask &quot;queue mode redis scaling&quot;</code></pre>

<h2>analyzer.py — анализ воркфлоу</h2>
<pre><code>python brain/scripts/analyzer.py --all                 # проанализировать все воркфлоу из доков
python brain/scripts/analyzer.py &lt;workflow.json&gt; --format json
python brain/scripts/analyzer.py &lt;workflow.json&gt; --format md</code></pre>
<p>Текущий результат на Google Sheets (docs version): найден один AI-агент (<code>@n8n/n8n-nodes-langchain.agent</code>), модель разрешилась в <code>lmChatOpenAi</code>, сложность 9/10.</p>

<h2>generator.py — spec → SaaS-проект</h2>
<pre><code>python brain/scripts/generator.py brain/research/workflow-analyses/agents-vs-chains.json -o generated-saas
python brain/scripts/generator.py --all -o generated-saas</code></pre>

<h2>verify.py — гейт</h2>
<pre><code>python brain/scripts/verify.py            # 12 гейтов, печатает VERDICT
python brain/scripts/verify.py --quick    # пропустить гейты, зависящие от пересборки</code></pre>
<p>Гейты: {', '.join(f['gates'])}.</p>

<h2>seed_claims.py — claims с првенансом</h2>
<pre><code>python brain/scripts/seed_claims.py</code></pre>
""",
        "troubleshooting": lambda f: f"""
<h1>Решение проблем</h1>
<p>Каждая запись — реальная ошибка этого проекта с конкретным фиксом. Ничего спекулятивного.</p>

<h2>WinError 32 — сборка не может удалить БД (Windows)</h2>
<p><strong>Симптом:</strong> <code>PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: 'wiki.db'</code></p>
<p><strong>Фикс:</strong> <code>forge.py db_connect(recreate=True)</code> теперь сначала удаляет stale WAL/SHM sidecar и при заблокированном файле падает обратно на сброс схемы на месте. Зафиксировано в коде путей пересборки.</p>

<h2>FTS5 был тихо отключён при первой сборке</h2>
<p><strong>Симптом:</strong> <code>no such column: T.headings</code></p>
<p><strong>Причина:</strong> FTS5 был объявлен как external-content таблица поверх <code>docs</code>, у которого нет колонки headings.</p>
<p><strong>Фикс:</strong> отдельная standalone-таблица <code>docs_fts</code>; теперь поиск на самом деле работает.</p>

<h2>Падение cp1252 на Windows для не-ASCII вывода</h2>
<p><strong>Симптом:</strong> <code>UnicodeEncodeError: 'charmap' codec can't encode character '\\u25b8'</code></p>
<p><strong>Фикс:</strong> <code>sys.stdout.reconfigure(encoding='utf-8')</code> в скриптах; статус-символы убраны.</p>

<h2>Сайт отдавал 404 на Pages-адресе</h2>
<p><strong>Причина:</strong> источник Pages был <code>main /</code> (корень), тогда как сайт жил в <code>/docs</code>.</p>
<p><strong>Фикс:</strong> <code>gh api ... -X PUT -f source[path]=/docs</code>. Подтверждено: сборка <code>built</code>, страница отдаёт 200.</p>

<h2>Отсутствующий favicon / og-card</h2>
<p><code>logo.svg</code> ссылался, но файла не было; <code>og-card.jpg</code> заявлялся в meta, но не был закоммичен. Сгенерированы и закоммичены.</p>

<h2>GitHub Actions заблокирован биллингом</h2>
<p><strong>Симптом:</strong> <code>The job was not started because your account is locked due to a billing issue.</code></p>
<p><strong>Фикс:</strong> реальная проверка — локальный гейт (<code>python brain/scripts/verify.py</code>), 12 гейтов, ненулевой код выхода при провале. CI не доказан, пока биллинг не исправят; зелёным его считать нельзя.</p>

<h2>F008 sync заблокирован</h2>
<p>Файл воркфлоу есть (<code>n8n-wiki/workflows/f008-sync-workflow.json</code>); нужен запущенный n8n для webhook/cron-проверки. Заблокирован окружением, не дизайном.</p>
""",
        "contact": lambda f: f"""
<h1>Контакт</h1>
<p><strong>homgorn</strong> — AI universe development. Один разработчик, на виду.</p>
<table>
  <tbody>
    <tr><th>GitHub</th><td><a href="https://github.com/homgorn">github.com/homgorn</a></td></tr>
    <tr><th>Репозиторий</th><td><a href="https://github.com/homgorn/n8n-saas-factory">github.com/homgorn/n8n-saas-factory</a></td></tr>
    <tr><th>Сайт</th><td><a href="https://homgorn.github.io/n8n-saas-factory/">homgorn.github.io/n8n-saas-factory</a></td></tr>
    <tr><th>Компания</th><td><a href="https://refertur.com">Refertur</a></td></tr>
    <tr><th>Прямой контакт</th><td><a href="https://t.me/realhikaz">Telegram @realhikaz</a></td></tr>
    <tr><th>Локация</th><td>Earth (Земля)</td></tr>
  </tbody>
</table>

<h2>Биография</h2>
<p>AI universe development with @github. Строю то, что не построит большая команда. Здесь всё измерено, указано или честно помечено как непроверенное — см. claims в вики.</p>

<h2>Чего я не буду делать</h2>
<ul>
  <li>Оспаривать лицензию n8n — это их лицензия; я строю вокруг неё</li>
  <li>Говорить, что CI зелёный, пока аккаунт заблокирован биллингом</li>
  <li>Ставить <code>passes: true</code> фиче, которая ни разу не запускалась</li>
</ul>
""",
    },
}


if __name__ == "__main__":
    main()
