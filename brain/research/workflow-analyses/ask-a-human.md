# Workflow Analysis: Ask a human

**Source**: `n8n-docs-source\docs\_workflows\advanced-ai\examples\ask_a_human.json`
**Workflow ID**: `2f12a354677a`
**Active**: False

## Summary

- **Trigger**: n8n-nodes-base.executeWorkflowTrigger (2 trigger(s))
- **Nodes**: 17 (1 flow control, 2 data transform, 3 AI components)
- **AI Agents**: 1
- **Credentials**: 0 types
- **Complexity**: 8.8/10
- **Estimated API endpoints**: 2
- **Estimated DB tables**: 3

## AI Agents

### AI Agent
- Type: `@n8n/n8n-nodes-langchain.agent`
- Model: `@n8n/n8n-nodes-langchain.lmChatOpenAi`
- Tools: ['@n8n/n8n-nodes-langchain.toolWorkflow']
- Memory: `@n8n/n8n-nodes-langchain.memoryBufferWindow`
- Output parser: `none`
- System prompt: n/a

## Environment variables

- `OPENAI_API_KEY`

## Data flow

`Execute Workflow Trigger` → `Check if user has provided email` → `Message Slack for help` → `Prompt the user to provide an email` → `Confirm that we've messaged a human`
