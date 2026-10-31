# Workflow Analysis: Populate a Pinecone vector database from a website

**Source**: `n8n-docs-source\docs\_workflows\advanced-ai\examples\populate_a_pinecone_vector_database_from_a_website.json`
**Workflow ID**: `f5f6c9213e2f`
**Active**: False

## Summary

- **Trigger**: @n8n/n8n-nodes-langchain.chatTrigger (2 trigger(s))
- **Nodes**: 31 (2 flow control, 1 data transform, 9 AI components)
- **AI Agents**: 0
- **Credentials**: 2 types
- **Complexity**: 8/10
- **Estimated API endpoints**: 2
- **Estimated DB tables**: 4

## Credentials

- `openAiApi`: used by Embeddings OpenAI, OpenAI Model, Embeddings OpenAI2
- `pineconeApi`: used by Pinecone Vector Store, Pinecone Vector Store2

## Environment variables

- `OPENAI_API_KEY`
- `PINECONE_API_KEY`

## Data flow

`Chat Trigger` → `Question and Answer Chain`
