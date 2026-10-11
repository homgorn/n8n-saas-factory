# Product Backlog

## Epic: n8n Documentation Intelligence Layer
**Goal**: Build searchable, queryable knowledge base from n8n docs

| ID | Title | Description | Priority | Estimate | Status |
|----|-------|-------------|----------|----------|--------|
| BACK-001 | Ingest all n8n docs from GitHub clone | Parse 1,925 markdown files, extract metadata, chunk semantically | P0 | 8h | 📋 Ready |
| BACK-002 | Ingest llms-full.txt paginated content | Fetch all 14 parts, merge with GitHub source | P0 | 4h | 📋 Ready |
| BACK-003 | Build vector database (Qdrant) | Store embeddings with full metadata payload | P0 | 6h | 📋 Ready |
| BACK-004 | Implement hybrid search (vector + keyword) | Combine semantic search with exact matching | P0 | 4h | 📋 Ready |
| BACK-005 | Build LLM query interface | Route queries, format responses with citations | P0 | 8h | 📋 Ready |
| BACK-006 | Add query classification router | Classify: how-to, node-ref, troubleshooting, architecture | P1 | 4h | 📋 Ready |
| BACK-007 | Implement daily sync from docs.n8n.io | Cron job to fetch updates, diff, update vector DB | P1 | 4h | 📋 Ready |
| BACK-008 | Add code example extraction | Parse code blocks, link to nodes/workflows | P1 | 4h | 📋 Ready |
| BACK-009 | Build evaluation dataset | 50 test queries with expected answers | P2 | 4h | 📋 Ready |
| BACK-010 | Add feedback loop | User ratings → improve retrieval | P2 | 4h | 📋 Ready |

## Epic: Workflow Analyzer
**Goal**: Parse n8n workflow JSON → structured analysis for SaaS generation

| ID | Title | Description | Priority | Estimate | Status |
|----|-------|-------------|----------|----------|--------|
| BACK-011 | Parse workflow JSON structure | Nodes, connections, credentials, settings | P0 | 4h | 📋 Ready |
| BACK-012 | Identify trigger type & API spec | Webhook path, method, auth, cron schedule | P0 | 3h | 📋 Ready |
| BACK-013 | Detect AI agents & configuration | Model, tools, system prompt, memory | P0 | 4h | 📋 Ready |
| BACK-014 | Map data flow & DB requirements | Input → transform → output, estimate tables | P0 | 4h | 📋 Ready |
| BACK-014 | Extract credentials & env vars | Required API keys, secrets, OAuth configs | P0 | 2h | 📋 Ready |
| BACK-015 | Calculate complexity score | Weighted: nodes, branches, AI agents, external calls | P1 | 2h | 📋 Ready |
| BACK-016 | Output analysis JSON schema | Standardized format for generator | P0 | 2h | 📋 Ready |

## Epic: SaaS Factory - Templates
**Goal**: Reusable templates for different SaaS types

| ID | Title | Description | Priority | Estimate | Status |
|----|-------|-------------|----------|----------|--------|
| BACK-017 | AI Tool Template (single workflow) | Next.js + n8n webhook + Supabase + Clerk + Stripe | P0 | 16h | 📋 Ready |
| BACK-018 | Automation Platform Template | Multi-workflow dashboard, execution history, scheduling | P1 | 24h | 📋 Ready |
| BACK-019 | Data Pipeline Template | ETL workflows, ClickHouse/Postgres, monitoring | P1 | 20h | 📋 Ready |
| BACK-020 | Agent Marketplace Template | Multi-agent, vector DB, usage billing | P2 | 32h | 📋 Ready |
| BACK-021 | Integration Hub Template | OAuth manager, connector marketplace | P2 | 24h | 📋 Ready |

## Epic: Workflow-to-Code Generator
**Goal**: Analysis JSON → Complete SaaS project

| ID | Title | Description | Priority | Estimate | Status |
|----|-------|-------------|----------|----------|--------|
| BACK-022 | Map analysis to template params | Transform workflow analysis → template variables | P0 | 4h | 📋 Ready |
| BACK-023 | Generate Next.js project structure | Copy template, replace placeholders | P0 | 4h | 📋 Ready |
| BACK-024 | Generate TypeScript types from workflow I/O | Input/output schemas → TS interfaces | P0 | 4h | 📋 Ready |
| BACK-025 | Create n8n workflow import script | Deploy workflow to target n8n instance | P0 | 3h | 📋 Ready |
| BACK-026 | Generate .env.example & README | All required vars, deployment instructions | P0 | 2h | 📋 Ready |
| BACK-027 | CLI entry point | `npx saas-factory generate <workflow.json> -o <dir>` | P0 | 3h | 📋 Ready |

## Epic: OpenChamber Integration
**Goal**: Orchestrate agents, sync with n8n/GitHub/Vercel

| ID | Title | Description | Priority | Estimate | Status |
|----|-------|-------------|----------|----------|--------|
| BACK-028 | Configure OpenChamber project | Project dir, sessions, artifacts | P0 | 2h | ✅ Done |
| BACK-029 | Add n8n MCP server | Workflow CRUD, executions, credentials | P0 | 4h | 📋 Ready |
| BACK-030 | Add GitHub MCP server | Repo, PRs, issues, actions | P0 | 3h | 📋 Ready |
| BACK-031 | Add Vercel MCP server | Deployments, domains, env vars | P0 | 3h | 📋 Ready |
| BACK-032 | Add Supabase MCP server | Database, auth, storage, realtime | P0 | 3h | 📋 Ready |
| BACK-033 | Add Stripe MCP server | Products, subscriptions, webhooks | P1 | 3h | 📋 Ready |
| BACK-034 | Register 7 agents | explorer, researcher, architect, implementer, verifier, reviewer, runner | P0 | 2h | ✅ Done |
| BACK-035 | Build sync workflows in n8n | Docs sync, workflow→code, deploy pipeline | P0 | 8h | 📋 Ready |

## Epic: Verification & Quality Gates
**Goal**: Automated verification before marking features done

| ID | Title | Description | Priority | Estimate | Status |
|----|-------|-------------|----------|----------|--------|
| BACK-036 | init.sh environment verification | Check tools, ports, env, start services | P0 | 3h | ✅ Done |
| BACK-037 | Verifier agent test patterns | Auth, webhook, dashboard, billing, landing | P0 | 4h | ✅ Done |
| BACK-038 | Thermo-nuclear review integration | Security, correctness, maintainability | P0 | 2h | ✅ Done |
| BACK-039 | Playwright smoke tests | Critical user journeys | P1 | 4h | 📋 Ready |
| BACK-040 | Git hooks (pre-commit, pre-push) | Lint, typecheck, test | P1 | 2h | 📋 Ready |

## Epic: Documentation & DX
**Goal**: Developer experience, onboarding, troubleshooting

| ID | Title | Description | Priority | Estimate | Status |
|----|-------|-------------|----------|----------|--------|
| BACK-041 | CLAUDE.md project overview | Key commands, architecture, workflows | P0 | 2h | 📋 Ready |
| BACK-042 | CONTRIBUTING.md agent workflow | How to use agents, PR process | P0 | 2h | 📋 Ready |
| BACK-043 | n8n wiki query API docs | REST endpoints, examples | P1 | 2h | 📋 Ready |
| BACK-044 | SaaS factory CLI docs | Commands, options, examples | P1 | 2h | 📋 Ready |
| BACK-045 | Troubleshooting guide | Common sync issues, fixes | P1 | 3h | 📋 Ready |
| BACK-046 | Video walkthrough | Full pipeline demo | P2 | 4h | 📋 Ready |

---

## Backlog Management

### Priority Definitions
- **P0** - Blocking: Must have for MVP
- **P1** - Important: Needed for production readiness
- **P2** - Nice to have: Post-MVP enhancements

### Status Definitions
- 📋 **Ready** - Well-defined, can start immediately
- 🔄 **In Progress** - Currently being worked on
- 👀 **In Review** - PR open, awaiting review
- ✅ **Done** - Verified and merged
- 🚫 **Blocked** - Waiting on dependency
- ❓ **Needs Clarification** - Requirements unclear

### Sprint Planning
- Sprint 1 (Week 1-2): BACK-001 to BACK-010 (Documentation Wiki)
- Sprint 2 (Week 2-3): BACK-011 to BACK-016 (Workflow Analyzer)
- Sprint 3 (Week 3-4): BACK-017 to BACK-021 (Templates)
- Sprint 4 (Week 4-5): BACK-022 to BACK-027 (Generator)
- Sprint 5 (Week 5-6): BACK-028 to BACK-035 (OpenChamber + Sync)
- Sprint 6 (Week 6-7): BACK-036 to BACK-040 (Quality Gates)
- Sprint 7 (Week 7-8): BACK-041 to BACK-046 (Documentation)