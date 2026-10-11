# n8n SaaS Factory

Turn an n8n workflow into a deployed SaaS product, with a queryable knowledge base over the n8n
documentation and agent orchestration through OpenChamber.

## What is here

```
brain/                    LLM wiki over the n8n docs — the retrieval layer
  scripts/forge.py        the generator (stdlib only, idempotent)
  wiki/<topic>/           1,348 pages across 11 domains
  index/                  topics.json · entities.json · graph.jsonl
  data/wiki.db            SQLite: docs, chunks, entities, triples, workflows, run_log
  INDEX.md                domain map          HANDOFF.md   cold-start brief

saas-factory/analyzer/    TypeScript ingestion pipeline (Qdrant + OpenAI embeddings) — in progress
generated-saas/           output: one SaaS per workflow
.openchamber/agents/      explorer · researcher · architect · implementer · verifier · reviewer · runner
.opencode/agents/         same roles for OpenCode
```

## The wiki

Built from `n8n-io/n8n-docs` (GitBook source), not scraped HTML. 1,348 pages, 9,578 chunks,
688k words, 2,966 entities, 2,552 triples, 12 importable workflow JSON.

```bash
python brain/scripts/forge.py build                        # regenerate everything
python brain/scripts/forge.py stats                        # corpus shape
python brain/scripts/forge.py query "pagination"            # page-level full-text search
python brain/scripts/forge.py ask "retry failed executions" # chunk-level, IDF-ranked
```

`ask` ranks with inverse document frequency and word-boundary matching, so a term that appears
everywhere contributes nothing and a substring inside another word does not match.

Retrieval today is SQLite FTS5 plus the JSON indexes. Vector search is not wired: it needs
`OPENAI_API_KEY` and a Qdrant instance. `saas-factory/analyzer` holds that pipeline.

## Provenance

Every claim carries a type, and only typed claims reach a page:

| type | meaning |
| --- | --- |
| `measured` | ran it, the artifact is named |
| `reported` | a source says it, URL + retrieval date |
| `inferred` | reasoned it, the reasoning is written out |
| `unconfirmed` | where it was looked for, not found |

`claims` is currently empty — nothing has been asserted yet. See [`brain/HANDOFF.md`](brain/HANDOFF.md).

## Agents

| agent | job | isolation |
| --- | --- | --- |
| `explorer` | read-only codebase mapping | no writes |
| `researcher` | search the wiki, the docs, the web | no writes |
| `architect` | workflow → SaaS spec, writes `SPEC.md` | writes specs |
| `implementer` | writes the code | scoped writes |
| `verifier` | proves a feature works end to end | **never writes** |
| `reviewer` | security and maintainability review | no writes |
| `runner` | runs builds and suites, reports failures only | no writes |

`verifier` returns `VERDICT: PASS | FAIL | BLOCKED`. A step it could not attempt is BLOCKED, not
PASS. It never repairs what it finds — a verifier that fixes its own findings stops being
independent.

## Verification

A feature is done when the gate passes, not when the code looks right:

```bash
./init.sh --check-only          # tools, ports, services
python brain/scripts/forge.py build
python brain/scripts/forge.py ask "how do I paginate API results"
```

Feature state lives in [`feature_list.json`](feature_list.json). Only `verifier` sets `passes: true`.

## Status

See [`CHANGELOG.md`](CHANGELOG.md), [`BACKLOG.md`](BACKLOG.md), [`ERROR_LOG.md`](ERROR_LOG.md)
and [`PROJECT_PLAN.md`](PROJECT_PLAN.md).

## Licence

Project code: see [`LICENSE`](LICENSE).

The n8n documentation under `n8n-docs-source/` is **not ours**. It is cloned from
`n8n-io/n8n-docs` and carries n8n's Sustainable Use License. See
[`privacy-and-security`](brain/wiki/privacy-and-security/00-INDEX.md). Cloning a repository to read
it for building a product is not the same as granting redistribution rights — confirm the terms
before publishing anything derived from it.