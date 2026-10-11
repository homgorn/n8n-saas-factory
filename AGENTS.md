# AGENTS.md - Agent Routing Configuration

## Project Overview
This project builds a SaaS factory that transforms n8n workflows into deployable SaaS products, with an internal n8n LLM wiki and OpenChamber orchestration.

## Agent Routing

Delegate by task shape, not by habit:

### Read-Only Agents (Cheap Models)
- **"Where is X?", "How does Y work?"** → `explorer` (read-only, cheap/fast)
- **"Search n8n docs for...", "Find pattern..."** → `researcher` (websearch, n8n-docs MCP)
- **Running builds or test suites** → `runner` (read-only, cheap; report only failures)

### Implementation Agents (Default Model)
- **Making changes for current feature** → `implementer` (scoped writes)
- **Generating code from templates** → `implementer`
- **Creating n8n workflows** → `implementer` (with n8n MCP)

### Verification Agents (Mandatory)
- **Before marking ANY feature done** → `verifier` (mandatory, read-only)
- **Testing deployed SaaS** → `verifier` (playwright, vercel MCP)
- **Code review** → `reviewer` (thermo-nuclear review)

### Specialist Agents
- **Architecture decisions** → `architect` (n8n MCP, read/write specs)
- **Adversarial review** → `critic` x N in parallel (strong model)
- **Bulk mechanical edits** → `migrator` (isolated copies)

## Agent Definitions

### explorer
```markdown
---
name: explorer
description: Read-only codebase mapping, answers "where is X", "how does Y work"
model: openrouter:deepseek/deepseek-chat-v3-0324:free
tools: [read, grep, glob, shell]
---
```

### researcher
```markdown
---
name: researcher
description: Research n8n documentation, find patterns, search web for solutions
model: openrouter:deepseek/deepseek-chat-v3-0324:free
tools: [read, grep, glob, websearch, webfetch, mcp:n8n-docs]
---
```

### architect
```markdown
---
name: architect
description: Design SaaS from n8n workflow, create specs, plan implementation
model: openrouter:anthropic/claude-3.5-sonnet:free
tools: [read, write, grep, glob, shell, mcp:n8n, mcp:github]
---
```

### implementer
```markdown
---
name: implementer
description: Implement features, generate code, create n8n workflows
model: openrouter:anthropic/claude-3.5-sonnet:free
tools: [read, write, edit, shell, mcp:n8n, mcp:github, mcp:vercel]
---
```

### verifier
```markdown
---
name: verifier
description: Prove a feature works end-to-end in the running app before marking done. Read-only.
model: openrouter:anthropic/claude-3.5-sonnet:free
tools: [read, grep, glob, shell, mcp:playwright, mcp:vercel, mcp:supabase]
---

You verify one feature and return a verdict. You never implement.

## Input
The feature id, its `steps` array from feature_list.json, and the current diff.

## Process
1. Run `init.sh` and confirm the environment is up.
2. Execute each step in `steps` literally, in order, as a user would.
3. For anything visual or interactive, drive the real app — a unit test is not verification.
4. For each step, record: pass, fail, or blocked, with the evidence.

## Output
A single verdict line, then the evidence.

VERDICT: PASS | FAIL | BLOCKED
- F001: pass — <evidence>
- F002: fail at step 3 — <what happened, expected vs actual>

## Rules
- Never fix anything. Report, do not repair.
- A step you could not attempt is BLOCKED, not PASS.
- Never mark a feature passing on the basis of the code looking correct.
```

### reviewer
```markdown
---
name: reviewer
description: Thermo-nuclear code review for security, correctness, maintainability
model: openrouter:anthropic/claude-3.5-sonnet:free
tools: [read, grep, glob, shell]
---
```

### runner
```markdown
---
name: runner
description: Run builds, test suites, noisy commands - report only failures
model: openrouter:deepseek/deepseek-chat-v3-0324:free
tools: [shell, read]
---
```

## Parallel Fan-Out Rules

Good fan-out shapes:
- One agent per file, results merged by architect
- Several critics on one question, then compare
- N independent drafts (implementer), then judge against each other

Every parallel agent that writes needs its own working copy (isolated git worktree).

## Verification Gate

The gate is the ONLY thing that stops the loop:
```bash
# Gate command (run by loop-until-done)
./init.sh && npm run typecheck && npm run test && npm run lint
```

Features are only marked `passes: true` AFTER verifier returns PASS.

## OpenChamber Integration

OpenChamber sessions spawn these agents automatically:
- Session created → architect analyzes workflow
- Feature picked → implementer spawned
- Feature implemented → verifier spawned
- PR opened → reviewer spawned
- Deploy triggered → verifier runs smoke tests

MCP servers available in all sessions:
- `n8n` - Workflow CRUD, executions, credentials
- `github` - Repo, PRs, issues
- `vercel` - Deployments, domains
- `supabase` - Database, auth
- `stripe` - Billing
- `playwright` - Browser automation