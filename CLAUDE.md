# CLAUDE.md — n8n SaaS Factory

## Project overview

This project builds a SaaS factory that transforms n8n workflows into deployable SaaS products.
It includes an internal LLM wiki over the n8n documentation, a workflow analyzer, a SaaS template
generator, and agent orchestration through OpenChamber.

**Licence constraint (ADR-001)**: n8n is under the Sustainable Use License. We do NOT host n8n.
The customer operates their own n8n instance; our product is the layer above it (dashboard, billing,
multi-tenancy, API). Read `brain/decisions/ADR-001-n8n-licence-blocks-hosted-saas.md` before
designing anything that touches n8n.

## Key commands

```bash
# Wiki
python brain/scripts/forge.py build          # regenerate wiki from n8n docs
python brain/scripts/forge.py stats          # corpus shape
python brain/scripts/forge.py query "term"   # page-level FTS search
python brain/scripts/forge.py ask "question" # chunk-level IDF-ranked search

# Claims
python brain/scripts/seed_claims.py          # record provenance-stamped claims

# Analyzer
python brain/scripts/analyzer.py --all       # analyze all 12 workflows

# Generator
python brain/scripts/generator.py --all -o generated-saas  # generate all SaaS projects

# Verification gate (run before declaring anything done)
python brain/scripts/verify.py              # 11 gates, prints VERDICT, exits non-zero on failure
python brain/scripts/verify.py --quick      # skip rebuild, 4 gates

# Environment
./init.sh                                   # start dev environment
./init.sh --check-only                      # verify tools/ports only
```

## Architecture

```
brain/                    LLM wiki over n8n docs (retrieval layer)
  scripts/forge.py        generator (stdlib only, idempotent)
  scripts/query.py        query interface (classify, search, format)
  scripts/analyzer.py     workflow analyzer
  scripts/generator.py    workflow-to-SaaS generator
  scripts/verify.py       verification gate (11 gates)
  scripts/seed_claims.py  provenance-stamped claims
  wiki/<topic>/           1348 pages across 11 domains
  index/                  topics.json, entities.json, graph.jsonl, claims.json
  data/wiki.db            SQLite corpus
  decisions/              ADR-001, ADR-002

saas-factory/
  templates/ai-tool/      Next.js 14 SaaS template (customer-runs-own-n8n)
  analyzer/               TypeScript ingestion pipeline (Qdrant + OpenAI) — supplementary

generated-saas/           Output: one SaaS project per workflow (12 generated)

.openchamber/
  agents/                 7 agent definitions (explorer, researcher, architect, implementer, verifier, reviewer, runner)
  mcp-servers.json        MCP server configuration
  agent-config.json       agent routing table
```

## Agent routing

Delegate by task shape, not by habit:
- "where is X", "how does Y work" → `explorer` (read-only, cheap)
- "search n8n docs", "find pattern" → `researcher` (websearch, wiki)
- architecture decisions → `architect` (n8n MCP, writes specs)
- making changes → `implementer` (scoped writes)
- before marking done → `verifier` (mandatory, read-only, never writes)
- code review → `reviewer` (thermo-nuclear)
- builds/tests → `runner` (reports failures only)

## Verification

A feature is done when `python brain/scripts/verify.py` prints `VERDICT: PASS`, not when the code
looks right. The gate checks: sources present, build idempotence, corpus floor, summaries within
200 chars, live source URLs, retrieval answers real questions, claims typed and sourced, no secrets,
licence documented, feature list honest, query interface works.

Only `verifier` may set `passes: true` in `feature_list.json`.

## Verification gate (current state)

```
11/11 gates passing
5 features passing: F002, F003, F004, F005, F006
```

## Key files

- `PROJECT_PLAN.md` — 6-phase plan, 10 features, risks, stack
- `feature_list.json` — feature state (only verifier sets passes: true)
- `BACKLOG.md` — 46 items in 8 epics
- `CHANGELOG.md` — keep-a-changelog format
- `ERROR_LOG.md` — centralized error tracking
- `AGENTS.md` — agent routing configuration
- `brain/HANDOFF.md` — cold-start brief for agents
- `brain/INDEX.md` — domain map
- `brain/decisions/ADR-001-*.md` — licence constraint
- `brain/decisions/ADR-002-*.md` — SaaS architecture