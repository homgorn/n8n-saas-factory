# Error Log

Centralized error tracking for development, deployment, and production issues.

## Format

```markdown
### [ERROR-ID] YYYY-MM-DD HH:MM - SEVERITY - COMPONENT
**Context**: What was happening
**Error**: Exact error message
**Stack Trace**: Relevant stack trace
**Root Cause**: Analysis
**Fix**: Solution applied
**Prevention**: How to avoid recurrence
**Related**: Linked issues, PRs, commits
```

---

## Development Errors

### [DEV-001] 2026-10-08 05:45 - HIGH - GIT CLONE
**Context**: Cloning n8n-docs repository
**Error**: `fatal: fetch-pack: unexpected disconnect while reading sideband packet`
**Root Cause**: Network timeout on large repo clone
**Fix**: Used `--depth 1` for shallow clone
**Prevention**: Always use `--depth 1` for initial clones of large repos
**Related**: PROJECT_PLAN.md Phase 1

### [DEV-002] 2026-10-08 05:50 - MEDIUM - POWERSHELL SYNTAX
**Context**: Running shell commands in PowerShell
**Error**: `The token '&&' is not a valid statement separator`
**Root Cause**: Using bash syntax (`&&`, `||`) in PowerShell
**Fix**: Use PowerShell syntax (`;`, `||` not supported, use `if ($LASTEXITCODE) { }`)
**Prevention**: Document shell requirements, use cross-platform scripts
**Related**: init.sh

---

## Template for New Errors

### [ERROR-ID] YYYY-MM-DD HH:MM - SEVERITY - COMPONENT
**Context**: 
**Error**: 
**Stack Trace**: 
**Root Cause**: 
**Fix**: 
**Prevention**: 
**Related**: 

---

## Severity Levels
- **CRITICAL** - Production down, data loss, security breach
- **HIGH** - Feature broken, blocks development
- **MEDIUM** - Degraded functionality, workaround exists
- **LOW** - Cosmetic, minor inconvenience

## Components
- **DOC-INGEST** - Documentation ingestion pipeline
- **VECTOR-DB** - Qdrant/Pinecone operations
- **QUERY-API** - LLM query interface
- **WORKFLOW-ANALYZER** - Workflow JSON parsing
- **TEMPLATE-GEN** - SaaS template generation
- **CODE-GEN** - Workflow-to-code generator
- **N8N-SYNC** - n8n synchronization workflows
- **OPENCHAMBER** - OpenChamber orchestration
- **MCP** - MCP server connections
- **DEPLOY** - Vercel/Railway/Render deployments
- **AUTH** - Clerk/Supabase/NextAuth
- **BILLING** - Stripe integration
- **DATABASE** - Supabase/Postgres operations
- **ENV** - Environment setup, init.sh

## Resolution Tracking

| Error ID | Date | Severity | Component | Status | Resolved Date |
|----------|------|----------|-----------|--------|---------------|
| DEV-001 | 2026-10-08 | HIGH | GIT | ✅ Resolved | 2026-10-08 |
| DEV-002 | 2026-10-08 | MEDIUM | SHELL | ✅ Resolved | 2026-10-08 |

---

## Error Patterns to Watch

### Network/Timeout
- Large file downloads (llms-full.txt parts)
- Git operations on large repos
- MCP server connection timeouts
- API rate limits (OpenAI, n8n Cloud)

### Authentication/Secrets
- Missing environment variables
- Expired API keys
- Incorrect credential references in n8n
- Stripe webhook signature verification failures

### Type/Build Errors
- TypeScript strict mode violations
- Missing type definitions for n8n workflow JSON
- Next.js App Router server/client component boundaries
- Zod schema mismatches

### Sync/State Issues
- n8n workflow version conflicts
- Git merge conflicts in generated code
- Vector DB stale data
- OpenChamber session state drift