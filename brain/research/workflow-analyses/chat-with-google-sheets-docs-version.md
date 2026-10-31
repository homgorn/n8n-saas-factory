# Workflow Analysis: Chat with Google Sheets (docs version)

**Source**: `n8n-docs-source\docs\_workflows\advanced-ai\examples\chat_with_google_sheets_docs_version.json`
**Workflow ID**: `e4b5683b0210`
**Active**: False

## Summary

- **Trigger**: n8n-nodes-base.executeWorkflowTrigger (2 trigger(s))
- **Nodes**: 23 (1 flow control, 4 data transform, 5 AI components)
- **AI Agents**: 1
- **Credentials**: 0 types
- **Complexity**: 9/10
- **Estimated API endpoints**: 2
- **Estimated DB tables**: 3

## AI Agents

### AI Agent
- Type: `@n8n/n8n-nodes-langchain.agent`
- Model: `@n8n/n8n-nodes-langchain.lmChatOpenAi`
- Tools: ['@n8n/n8n-nodes-langchain.toolWorkflow', '@n8n/n8n-nodes-langchain.toolWorkflow', '@n8n/n8n-nodes-langchain.toolWorkflow']
- Memory: `@n8n/n8n-nodes-langchain.memoryBufferWindow`
- Output parser: `none`
- System prompt: ={{ $json.chatInput }}

## Environment variables

- `OPENAI_API_KEY`

## Data flow

`Execute Workflow Trigger` → `Set Google Sheet URL` → `Get Google sheet contents` → `Check operations` → `Get column names` → `Prepare column data` → `Filter out other rows` → `Prepare output`
