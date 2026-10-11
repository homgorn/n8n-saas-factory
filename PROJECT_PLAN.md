# n8n SaaS Builder - Comprehensive Project Plan

## Executive Summary

This project creates a complete ecosystem for building SaaS products from n8n workflows, featuring:
1. **Internal LLM Wiki/Database** - Structured knowledge base from n8n docs
2. **SaaS Factory** - Transform n8n workflows into deployable SaaS products
3. **OpenChamber Integration** - Collaborative development and orchestration platform

---

## Phase 1: n8n Documentation Intelligence Layer (Weeks 1-2)

### 1.1 Documentation Ingestion Pipeline

**Source Materials:**
- Local clone: `C:\susa ai\N8N\n8n-docs-source\docs\` (1,925 markdown files)
- Online: `https://docs.n8n.io/llms-full.txt` (14-part paginated)
- Sitemap: `https://docs.n8n.io/sitemap.md` (1,394 entries)

**Pipeline Architecture:**
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  Sources    │────▶│  Extractor   │────▶│  Chunker    │────▶│  Embedder    │
│  (GitHub,   │     │  (Firecrawl  │     │  (Semantic  │     │  (OpenAI/    │
│   llms.txt) │     │   + Local)   │     │   + Code)   │     │   Local)     │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
                                                                       │
                                                                       ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Vector    │◀────│  Validator   │◀────│  Enricher   │◀────│  Indexer     │
│   DB        │     │  (Schema)    │     │  (Metadata) │     │  (Qdrant/    │
│  (Qdrant)   │     └──────────────┘     └─────────────┘     │   Pinecone)  │
└─────────────┘                                               └──────────────┘
```

### 1.2 Knowledge Categories & Structure

| Category | Source Paths | Est. Pages | Priority |
|----------|--------------|------------|----------|
| **Core Concepts** | `get-started/`, `build/understand-workflows/` | ~50 | P0 |
| **Deployment** | `deploy/host-n8n/`, `deploy/use-n8n-cloud/` | ~80 | P0 |
| **Workflow Building** | `build/flow-logic/`, `build/work-with-data/` | ~120 | P0 |
| **AI Integration** | `build/integrate-ai/` | ~60 | P0 |
| **Nodes Reference** | `integrations/builtin/core-nodes/`, `app-nodes/` | ~400 | P1 |
| **API & CLI** | `connect/n8n-api/`, `deploy/host-n8n/use-the-command-line/` | ~30 | P1 |
| **Security & Scaling** | `deploy/host-n8n/configure-n8n/security/`, `scaling/` | ~40 | P1 |
| **Workflows/Templates** | `_workflows/`, `build/manage-workflows/n8n-packages/` | ~50 | P2 |
| **Node Development** | `connect/create-nodes/` | ~40 | P2 |

### 1.3 Enrichment Metadata Schema

```yaml
# Per-document metadata
document_id: "n8n-docs-build-flow-logic-split-with-conditionals"
source_url: "https://docs.n8n.io/build/flow-logic/split-with-conditionals.md"
category: "flow-logic"
subcategory: "conditionals"
tags: ["if-node", "switch-node", "branching", "workflow-logic"]
difficulty: "beginner"  # beginner, intermediate, advanced
prerequisites: ["build-your-first-workflow", "understand-workflows"]
related_nodes: ["n8n-nodes-base.if", "n8n-nodes-base.switch"]
code_examples: true
has_workflow_template: false
last_updated: "2026-10-08"
version: "1.0"

# Chunk-level metadata
chunk_id: "n8n-docs-build-flow-logic-split-with-conditionals-chunk-3"
chunk_type: "code_example"  # prose, code_example, configuration, warning, tip
parent_section: "Using the Switch Node"
token_count: 245
```

### 1.4 Vector Database Design

**Collection: `n8n_knowledge_base`**
- Vector size: 1536 (text-embedding-3-small) or 3072 (text-embedding-3-large)
- Distance: Cosine
- Payload fields: All metadata above + full text

**Additional Collections:**
- `n8n_nodes_reference` - Node-specific docs with parameters, examples
- `n8n_workflow_patterns` - Extracted patterns from `_workflows/`
- `n8n_code_snippets` - Code node examples, expressions, JMESPath queries

---

## Phase 2: LLM Query Interface (Week 2-3)

### 2.1 Query Types Supported

| Query Type | Example | Implementation |
|------------|---------|----------------|
| **How-to** | "How do I paginate with HTTP Request node?" | RAG + code examples |
| **Node Reference** | "What parameters does the Slack node have?" | Structured lookup + vector search |
| **Troubleshooting** | "Why does my workflow fail at the If node?" | Error patterns + solutions |
| **Architecture** | "How to scale n8n for 10k executions/day?" | Multi-doc synthesis |
| **Best Practices** | "Best way to handle secrets in production?" | Curated guidelines |
| **Migration** | "Moving from Zapier to n8n - what's different?" | Comparison framework |

### 2.2 Response Format

```markdown
## Answer
[Direct answer with citations]

## Relevant Documentation
- [Split with Conditionals](https://docs.n8n.io/build/flow-logic/split-with-conditionals.md) - Sections 2.1, 3.2
- [If Node Reference](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.if.md)

## Code Example
```javascript
// From n8n docs: HTTP Request node pagination
const response = await $http.request({
  method: 'GET',
  url: 'https://api.example.com/items',
  qs: { page: $page, limit: 100 }
});
```

## Related Workflows
- [Pagination Example](https://n8n.io/workflows/1234-pagination-pattern)

## Next Steps
1. Try the [quickstart workflow](https://docs.n8n.io/build-your-first-workflow.md)
2. Explore [flow logic patterns](https://docs.n8n.io/build/flow-logic.md)
```

---

## Phase 3: SaaS Factory - Workflow to Product (Weeks 3-6)

### 3.1 SaaS Architecture from n8n Workflows

```
┌─────────────────────────────────────────────────────────────────┐
│                      n8n Workflow (Source)                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│  │ Trigger │─▶│ Process │─▶│  AI/    │─▶│ Output  │             │
│  │ (Webhook│  │ Data    │  │ Logic   │  │ (API/   │             │
│  │  /Cron) │  │ Transform│  │         │  │ Webhook)│             │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SaaS Factory Pipeline                        │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │  Analyzer  │ │  Extractor │ │  Generator │ │  Deployer  │   │
│  │  (AST +    │ │  (API spec,│ │  (Next.js  │ │  (Vercel/  │   │
│  │   Graph)   │  │  Auth, DB) │  │  + API +   │  │  Cloudflare/│   │
│  └────────────┘ └────────────┘  │  Auth + DB)│  │  Render)   │   │
│                                └────────────┘ └────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Generated SaaS                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Frontend│ │   API    │ │   Auth   │ │  Billing │           │
│  │ (Landing,│ │  (REST/  │ │ (Clerk/  │ │ (Stripe/ │           │
│  │  Dashboard)│  GraphQL)│  │  NextAuth)│ │  Lemon)  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Workflow Analysis & Extraction

**Input:** n8n workflow JSON (exported `.json` or via n8n API)

**Analysis Output:**
```json
{
  "workflow_id": "wf_abc123",
  "name": "AI Content Generator",
  "trigger_type": "webhook",
  "trigger_config": { "path": "generate", "method": "POST" },
  "nodes": [
    {
      "id": "node_1",
      "type": "n8n-nodes-base.httpRequest",
      "name": "Call OpenAI",
      "parameters": { "url": "https://api.openai.com/v1/chat/completions", ... },
      "credentials": "openaiApi",
      "position": { "x": 200, "y": 100 }
    }
  ],
  "connections": { ... },
  "ai_agents": [
    {
      "node_id": "node_3",
      "type": "langchain_agent",
      "model": "gpt-4o",
      "tools": ["web_search", "code_execution"],
      "system_prompt": "..."
    }
  ],
  "required_credentials": ["openaiApi", "supabaseApi"],
  "environment_variables": ["OPENAI_API_KEY", "SUPABASE_URL"],
  "data_flow": "input → transform → ai_process → output",
  "complexity_score": 7.2,
  "estimated_api_endpoints": 3,
  "estimated_db_tables": 4
}
```

### 3.3 SaaS Generation Templates

| Template | Use Case | Stack |
|----------|----------|-------|
| **AI Tool SaaS** | Single AI workflow → API | Next.js + n8n webhook + Supabase |
| **Automation Platform** | Multi-workflow → Dashboard | Next.js + n8n API + Postgres + Auth |
| **Data Pipeline** | ETL/ELT workflows | Next.js + n8n + ClickHouse/Postgres |
| **Agent Marketplace** | Multiple AI agents | Next.js + n8n + Vector DB + Billing |
| **Integration Hub** | Connect N services | Next.js + n8n + OAuth manager |

### 3.4 Generated Project Structure

```
generated-saas/
├── apps/
│   ├── web/                 # Next.js 14+ App Router
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── (auth)/
│   │   │   │   │   ├── login/
│   │   │   │   │   ├── register/
│   │   │   │   │   └── callback/
│   │   │   │   ├── (dashboard)/
│   │   │   │   │   ├── workflows/
│   │   │   │   │   ├── executions/
│   │   │   │   │   ├── settings/
│   │   │   │   │   └── billing/
│   │   │   │   ├── api/
│   │   │   │   │   ├── webhooks/
│   │   │   │   │   │   └── n8n/[workflowId]/route.ts
│   │   │   │   │   ├── workflows/
│   │   │   │   │   └── auth/
│   │   │   │   └── page.tsx          # Landing page
│   │   │   ├── components/
│   │   │   ├── lib/
│   │   │   │   ├── n8n-client.ts
│   │   │   │   ├── auth.ts
│   │   │   │   ├── db.ts
│   │   │   │   └── billing.ts
│   │   │   └── types/
│   │   └── package.json
│   └── n8n/                 # n8n instance (embedded or external)
│       ├── docker-compose.yml
│       ├── workflows/       # Imported workflows
│       └── custom-nodes/    # Any custom nodes needed
├── packages/
│   ├── shared-types/
│   ├── n8n-sdk/            # TypeScript SDK for n8n API
│   └── ui-components/
├── turbo.json
├── package.json
└── README.md
```

---

## Phase 4: OpenChamber Integration (Weeks 4-5)

### 4.1 OpenChamber as Orchestration Layer

```
┌────────────────────────────────────────────────────────────┐
│                    OpenChamber Project                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Sessions   │  │  Scheduler  │  │  File System        │  │
│  │  (Agents)   │  │  (Cron)     │  │  (Artifacts)        │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         ▼                ▼                     ▼             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              MCP Servers (Connected)                     │  │
│  │  • n8n MCP (workflow CRUD, executions)                  │  │
│  │  • GitHub MCP (repo ops, PRs)                           │  │
│  │  • Vercel/Cloudflare MCP (deployments)                  │  │
│  │  • Supabase/Postgres MCP (database)                     │  │
│  │  • Stripe MCP (billing)                                 │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

### 4.2 Agent Roles for SaaS Development

| Agent | Role | Tools | Trigger |
|-------|------|-------|---------|
| **architect** | Design SaaS from workflow | read, grep, write, mcp:n8n | `/architect <workflow.json>` |
| **implementer** | Generate Next.js + n8n code | write, shell, mcp:github | Feature ticket |
| **verifier** | Test deployed SaaS | shell, mcp:vercel, playwright | Post-deploy |
| **researcher** | Find patterns, nodes, solutions | websearch, mcp:n8n-docs | Questions |
| **reviewer** | Code review, security audit | read, grep, thermo-nuclear | PR opened |

### 4.3 Session Workflow

```bash
# 1. Create project session
openchamber session create --project n8n-saas-factory --prompt "Build SaaS from workflow wf_abc123"

# 2. Spawn architect agent
openchamber session send --session <id> --prompt "/architect Analyze workflow wf_abc123 and design SaaS"

# 3. Architect creates spec → saves to files
# 4. Spawn implementer agents in parallel for each feature
# 5. Verifier tests each feature
# 6. Deploy via MCP
```

### 4.4 Persistent State Management

```
.openchamber/
├── projects/
│   └── n8n-saas-factory/
│       ├── sessions/
│       ├── artifacts/
│       │   ├── workflows/        # Imported n8n workflows
│       │   ├── generated-code/   # Generated SaaS code
│       │   ├── specs/            # Architecture specs
│       │   └── deployments/      # Deployment records
│       ├── knowledge/
│       │   └── n8n-wiki/         # Synced vector DB snapshot
│       └── config/
│           ├── mcp-servers.json
│           └── agent-config.json
```

---

## Phase 5: Synchronization & Automation (Weeks 5-6)

### 5.1 Bidirectional Sync: n8n ↔ OpenChamber ↔ GitHub

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   n8n       │◀───▶│  OpenChamber │◀───▶│  GitHub     │
│  (Source)   │     │  (Orchestrator)│    │  (Source    │
│             │     │              │     │   of Truth) │
│ • Workflows │     │ • Agents     │     │             │
│ • Credentials│    │ • Sessions   │     │ • Code      │
│ • Executions │    │ • Artifacts  │     │ • Issues    │
└─────────────┘     └──────────────┘     └─────────────┘
       │                   │                    │
       │                   │                    │
       ▼                   ▼                    ▼
┌────────────────────────────────────────────────────────────┐
│              Sync Engine (n8n-automation workflow)         │
│  • Watch n8n for workflow changes → Git commit             │
│  • Watch GitHub for code changes → Update n8n workflow     │
│  • Watch OpenChamber sessions → Update project state       │
│  • Scheduled: Daily wiki refresh from docs.n8n.io          │
└────────────────────────────────────────────────────────────┘
```

### 5.2 Sync Workflows (n8n)

**Workflow 1: Documentation Sync (Daily Cron)**
```
Schedule (Daily 2AM) → HTTP Request (llms.txt) → Diff → 
  → Update Vector DB → Notify OpenChamber (session message)
```

**Workflow 2: Workflow → Code Sync**
```
n8n Webhook (workflow.updated) → Analyze workflow → 
  → Generate diff → Create GitHub PR → Notify OpenChamber
```

**Workflow 3: Deployment Pipeline**
```
GitHub Push (main) → Vercel Deploy → Health Check → 
  → Update n8n webhook URLs → Notify stakeholders
```

### 5.3 OpenChamber Automation Skills

```yaml
# .openchamber/skills/n8n-saas-sync.yaml
name: n8n-saas-sync
version: 1.0.0
description: Sync n8n workflows, docs, and generated SaaS code

triggers:
  - type: schedule
    cron: "0 2 * * *"  # Daily docs sync
  - type: webhook
    path: "/n8n/webhook/workflow-changed"
  - type: github
    events: [push, pull_request]

actions:
  - name: sync-documentation
    agent: researcher
    prompt: |
      Fetch latest n8n docs from llms-full.txt, compare with local wiki,
      update vector database, report changes.
    
  - name: workflow-to-code
    agent: architect
    prompt: |
      Analyze changed workflow, generate updated SaaS code,
      create PR with changes.
      
  - name: deploy-and-verify
    agent: verifier
    prompt: |
      Deploy preview, run smoke tests, report status.
```

---

## Phase 6: SaaS Product Features (Week 6+)

### 6.1 Core SaaS Features (Generated)

| Feature | Implementation | n8n Source |
|---------|----------------|------------|
| **Auth** | Clerk/NextAuth + n8n user sync | User management workflow |
| **Billing** | Stripe + webhook → n8n | Subscription workflow |
| **Dashboard** | Next.js + n8n executions API | Execution monitoring workflow |
| **Workflow Builder** | Embedded n8n canvas (OEM) | n8n OEM mode |
| **API Keys** | Custom n8n credentials + API | Credential management |
| **Usage Analytics** | PostHog + n8n insights | Insights workflow |
| **Team/Projects** | n8n projects + RBAC | Project workflow |

### 6.2 Landing Page Generation (saas-landing-pages skill)

Using the loaded skill, generate:
- **Homepage** - Hero, features, social proof, CTA
- **Pricing Page** - Tiers, FAQ, comparison
- **Docs Portal** - Auto-generated from n8n wiki
- **Changelog** - From GitHub releases
- **Comparison Pages** - vs Zapier, Make, etc.

---

## Technical Stack Summary

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Vector DB** | Qdrant (local) / Pinecone (cloud) | Filterable metadata, hybrid search |
| **Embeddings** | text-embedding-3-small (cost) / large (quality) | OpenAI standard |
| **LLM** | GPT-4o / Claude 3.5 Sonnet | Best for code + reasoning |
| **Framework** | Next.js 14+ App Router | React Server Components, SEO |
| **Auth** | Clerk | Drop-in, supports orgs, B2B |
| **Database** | Supabase (Postgres) | Auth + DB + Realtime + Edge |
| **Deployment** | Vercel (web) + Railway/Render (n8n) | Native Next.js, easy n8n hosting |
| **Orchestration** | OpenChamber + n8n | Agent sessions + workflow automation |
| **Payments** | Stripe | Market leader, n8n node exists |
| **Monitoring** | PostHog + Sentry | Product analytics + error tracking |

---

## File Structure (Final)

```
C:\susa ai\N8N\
├── n8n-docs-source/           # Cloned documentation (source of truth)
├── n8n-wiki/                  # Internal LLM wiki (generated)
│   ├── vector-db/             # Qdrant data
│   ├── index/                 # Search indexes
│   ├── metadata/              # Enriched metadata JSON
│   └── refresh-logs/          # Sync history
├── saas-factory/              # Workflow → SaaS generator
│   ├── analyzer/              # Workflow analysis engine
│   ├── templates/             # SaaS templates
│   ├── generators/            # Code generators
│   └── cli.ts                 # CLI entry point
├── generated-saas/            # Output SaaS projects
│   └── <project-name>/
├── openchamber-project/       # OpenChamber integration
│   ├── .openchamber/
│   ├── agents/
│   ├── skills/
│   ├── mcp-servers/
│   └── sync-workflows/        # n8n workflows for sync
├── PROJECT_PLAN.md            # This file
├── feature_list.json          # project-init feature list
├── AGENTS.md                  # Agent routing
├── init.sh                    # Environment setup
└── progress.md                # Build progress log
```

---

## Milestones & Gates

| Milestone | Gate Criteria | Target |
|-----------|---------------|--------|
| **M1: Wiki Operational** | Query "How to paginate HTTP Request?" returns correct answer with citations | Week 2 |
| **M2: Workflow Analyzer** | Input workflow JSON → outputs structured analysis with 90% accuracy | Week 3 |
| **M3: First SaaS Generated** | Workflow → Deployed Next.js app with auth, API, billing | Week 5 |
| **M4: OpenChamber Integrated** | Agents can read/write n8n, GitHub, Vercel via MCP | Week 5 |
| **M5: Bidirectional Sync** | Change in n8n → Git PR → Deploy → n8n webhook updated | Week 6 |
| **M6: Production Ready** | 3+ SaaS products generated, documented, deployed | Week 8 |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| n8n API changes break sync | Medium | High | Version pinning, integration tests |
| Vector DB costs at scale | Low | Medium | Qdrant local, batch embeddings |
| OpenChamber MCP stability | Medium | Medium | Fallback to direct API calls |
| Generated code quality | High | High | Verifier agent, thermo-nuclear review |
| Credential management | High | Critical | External secrets (1Password/Vault) |

---

## Next Immediate Actions

1. **Create feature_list.json** using project-init skill
2. **Build documentation ingestion script** using universal-scraping-architect
3. **Set up Qdrant + embedding pipeline** 
4. **Create first n8n sync workflow** in n8n-docs-source
5. **Initialize OpenChamber project** with n8n MCP
6. **Define agent configurations** in AGENTS.md

---

## Questions for Clarification

Before proceeding, I need your input on:

1. **Deployment Target**: Self-hosted n8n (Docker) or n8n Cloud for the SaaS runtime?
2. **Scale Target**: How many concurrent SaaS products / workflows initially?
3. **Auth Preference**: Clerk, NextAuth, or Supabase Auth?
4. **Database**: Supabase (Postgres) or direct PostgreSQL?
5. **Billing**: Stripe only or also LemonSqueezy/Paddle?
6. **OpenChamber**: Already have an instance running, or need setup?
7. **Team Size**: Solo or team collaboration features needed?
8. **Custom Nodes**: Will SaaS products need custom n8n nodes?

Please answer these so I can tailor the implementation plan and start Phase 1 execution.