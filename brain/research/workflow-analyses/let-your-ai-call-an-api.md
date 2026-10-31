# Workflow Analysis: Let your AI call an API

**Source**: `n8n-docs-source\docs\_workflows\advanced-ai\examples\let_your_ai_call_an_api.json`
**Workflow ID**: `eb50d236c55e`
**Active**: False

## Summary

- **Trigger**: n8n-nodes-base.executeWorkflowTrigger (2 trigger(s))
- **Nodes**: 21 (0 flow control, 1 data transform, 8 AI components)
- **AI Agents**: 1
- **Credentials**: 0 types
- **Complexity**: 8/10
- **Estimated API endpoints**: 2
- **Estimated DB tables**: 3

## AI Agents

### AI Agent
- Type: `@n8n/n8n-nodes-langchain.agent`
- Model: `@n8n/n8n-nodes-langchain.lmChatOpenAi`
- Tools: ['@n8n/n8n-nodes-langchain.toolWorkflow']
- Memory: `@n8n/n8n-nodes-langchain.memoryBufferWindow`
- Output parser: `none`
- System prompt: ={{ $json.chatInput }}

## Environment variables

- `OPENAI_API_KEY`

## Data flow

`Execute Workflow Trigger` → `Work out activity type and number of people` → `Call the API` → `Set 'response' value`
