# Contributing to n8n SaaS Factory

## Getting started

1. Clone the repository:
   ```bash
   git clone https://github.com/homgorn/n8n-saas-factory.git
   cd n8n-saas-factory
   ```

2. Clone the n8n docs source (required for the wiki):
   ```bash
   git clone --depth 1 https://github.com/n8n-io/n8n-docs.git n8n-docs-source
   ```

3. Run the verification gate:
   ```bash
   python brain/scripts/verify.py
   ```

4. Read `CLAUDE.md` for project overview and key commands.

## Development workflow

### Using agents

This project uses specialized agents. Delegate by task shape:

- **explorer** (read-only, cheap) — "where is X?", "how does Y work?"
- **researcher** (read-only) — search n8n docs, find patterns
- **architect** (writes specs) — design decisions, SPEC.md
- **implementer** (writes code) — feature implementation
- **verifier** (read-only, mandatory) — proves feature works end-to-end
- **reviewer** (read-only) — security and maintainability review
- **runner** (read-only, cheap) — builds, tests, reports failures

### Feature workflow

1. **Pick a feature** from `feature_list.json` (highest priority, `passes: false`)
2. **Architect** writes `SPEC.md` with design and feature breakdown
3. **Implementer** writes code, commits, pushes branch
4. **Runner** runs typecheck + lint + test
5. **Reviewer** does thermo-nuclear code review
6. **Verifier** deploys preview, runs smoke tests, returns `VERDICT: PASS | FAIL | BLOCKED`
7. If PASS → merge PR → mark `passes: true` in `feature_list.json`

### Verification

A feature is done when `python brain/scripts/verify.py` prints `VERDICT: PASS`.
The gate checks: sources present, build idempotence, corpus floor, summaries, URLs,
retrieval, claims, secrets, licence, feature list, query interface.

**Only `verifier` may set `passes: true`.** Never mark a feature passing on the basis
of the code looking correct.

### Commit messages

Follow conventional commits:
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `chore:` maintenance
- `research:` research findings

Include the feature ID when applicable: `feat(F003): workflow analyzer`

### Pull requests

1. Create a branch: `git checkout -b feature/FXXX-description`
2. Implement the feature
3. Run `python brain/scripts/verify.py`
4. Open PR with description linking to the feature
5. Wait for reviewer + verifier approval

### Adding claims

Every factual claim in documentation must be typed and sourced:

| type | meaning |
| --- | --- |
| `measured` | ran it, the artifact is named |
| `reported` | a source says it, URL + retrieval date |
| `inferred` | reasoned it, the reasoning is written out |
| `unconfirmed` | looked for it, not found |

Add claims via `brain/scripts/seed_claims.py` and run `forge.py build` to regenerate.

### Adding ADRs

Architecture decisions go in `brain/decisions/ADR-NNN-short-slug.md` with:
- Status, date, deciders
- Context, decision, consequences
- Alternatives rejected
- Verification checklist
- Confidence level (0-10)

### Licence

This project's code is MIT. The n8n documentation under `n8n-docs-source/` is **not ours** —
it carries n8n's Sustainable Use License. Do not redistribute it without checking the terms.
Our SaaS products call a n8n instance the customer operates under their own licence (ADR-001).