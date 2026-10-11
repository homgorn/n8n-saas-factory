# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `brain/` — LLM wiki over the n8n documentation, generated and regenerable
  - `scripts/forge.py` (stdlib only, idempotent): `build | stats | query | ask`
  - 1,348 pages, 9,578 chunks, 688,466 words, 11 domains, 12 importable workflow JSON
  - four index levels: `INDEX.md` → `wiki/<topic>/00-INDEX.md` → `wiki/<topic>/<slug>.md` → `index/topics.json`
  - SQLite `brain/data/wiki.db`: `docs`, `chunks`, `entities`, `triples`, `claims`, `workflows`, `run_log`
  - knowledge graph in `index/graph.jsonl` (`subject | predicate | object | source`)
- `brain/scripts/seed_claims.py` — provenance-stamped claims, typed
  `measured | reported | inferred | unconfirmed`; 7 claims recorded
- `brain/scripts/verify.py` — the verification gate, runnable without GitHub Actions.
  10 gates: sources present · build idempotence · corpus floor · summaries within 200 chars ·
  live source URLs · retrieval answers real questions · claims typed and sourced ·
  no secrets · licence documented · feature list honest.
  Prints `VERDICT: PASS | FAIL` and exits non-zero on failure, so nothing downstream can
  infer success from the agent's own say-so.
- `brain/decisions/ADR-001-n8n-licence-blocks-hosted-saas.md`
- `.github/workflows/verify.yml` — CI: wiki build with a corpus floor, retrieval smoke test,
  secret scan, licence-documentation gate
- `.gitignore` — excludes the SQLite binary, `node_modules`, and the vendored docs clone
- `README.md`, `LICENSE`, `.env.example`

### Changed
- **Architecture changed by ADR-001.** The default SaaS shape was "we host n8n". n8n is licensed
  under the Sustainable Use License, which does not permit providing it to third parties for
  profit. The shape is now: the customer operates their own n8n instance and our product is the
  layer above it. See the ADR for the reasoning and the cost of that change.

### Fixed
- Retrieval ranking. `ask` scored substring occurrences, so `results` matched inside `several` and a
  DigitalOcean deployment page outranked the HTTP Request pagination section. Now inverse document
  frequency with word-boundary matching, diminishing returns per term, and a heavy weight on
  heading matches — a chunk headed "Retry failed workflows" now outranks a page that merely
  mentions "error" once. Stopwords are dropped: "how" was previously scoring 8× on titles.
- Claims were wiped by every rebuild, because they lived only in the recreated database. They are
  now re-applied from `brain/index/claims.json`, which is authored and lives in git.
- `forge.py build` crashed with `WinError 32` on Windows: a stale WAL sidecar held the database
  handle open, so the recreate path could not unlink it. It now clears the sidecars and falls back
  to dropping tables rather than deleting the file.
- Wiki build dropped the `_workflows` corpus because those files are JSON, not Markdown. They are now
  indexed into a `workflows` table — the most useful corpus in the repo for the workflow analyser.
- Node entity names were wrong: `n8n-nodes-langchain.agent` was recorded as `n8n-nodes-base.agent`,
  because the family was guessed from surrounding text. The family is now parsed from the match.
- FTS5 was silently disabled: it was declared as an external-content table over `docs`, which has
  no `headings` column. It is now a standalone FTS5 table and search actually runs.

### Known issues
- GitHub Actions cannot run on this account: *"The job was not started because your account is
  locked due to a billing issue."* `.github/workflows/verify.yml` is committed and correct, but it
  has never executed. `brain/scripts/verify.py` is the local equivalent and is what the 10/10 gate
  result above comes from. Until billing is resolved, CI is unproven — do not assume it is green.

### Security
- Licence position documented in README, LICENSE and `.env.example`, and enforced by a CI gate.
  n8n is not MIT and `n8n-docs-source/` is not ours to redistribute.
- Secret scan uses context-aware matching: a base64 line is only a finding when a `PRIVATE KEY`
  header sits within three lines above it, so the public certificate example in the SSL docs does
  not fail the build.

---

## [0.1.0] - 2026-10-08

### Added
- Initial project scaffold
- n8n documentation cloned from GitHub (n8n-docs-source/)
- Comprehensive PROJECT_PLAN.md with 6 phases
- Feature list with 10 prioritized features (F001-F010)
- Agent routing for 7 specialized agents
- init.sh for environment setup
- .loop/state.json for autonomous iteration tracking

---

## Release Template

## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Vulnerability fixes