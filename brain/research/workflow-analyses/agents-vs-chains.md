# Workflow Analysis: Agents vs chains

**Source**: `n8n-docs-source\docs\_workflows\advanced-ai\examples\agents_vs_chains.json`
**Workflow ID**: `qK43vJw6dRZkXo6h`
**Active**: False

## Summary

- **Trigger**: @n8n/n8n-nodes-langchain.chatTrigger (1 trigger(s))
- **Nodes**: 14 (1 flow control, 0 data transform, 5 AI components)
- **AI Agents**: 1
- **Credentials**: 1 types
- **Complexity**: 8.5/10
- **Estimated API endpoints**: 1
- **Estimated DB tables**: 4

## AI Agents

### AI Agent
- Type: `@n8n/n8n-nodes-langchain.agent`
- Model: `@n8n/n8n-nodes-langchain.lmChatOpenAi`
- Tools: ['@n8n/n8n-nodes-langchain.toolWikipedia']
- Memory: `@n8n/n8n-nodes-langchain.memoryBufferWindow`
- Output parser: `none`
- System prompt: n/a

## Credentials

- `openAiApi`: used by OpenAI Chat Model, OpenAI Chat Model1

## Environment variables

- `OPENAI_API_KEY`

## Data flow

`Chat Trigger` → `Check user input for "chain" or "agent"` → `AI Agent` → `Basic LLM Chain`
