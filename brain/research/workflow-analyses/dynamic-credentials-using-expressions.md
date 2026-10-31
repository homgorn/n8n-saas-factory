# Workflow Analysis: Dynamic credentials using expressions

**Source**: `n8n-docs-source\docs\_workflows\credentials\dynamic_credentials_using_expressions.json`
**Workflow ID**: `62019f24eac4`
**Active**: False

## Summary

- **Trigger**: n8n-nodes-base.formTrigger (1 trigger(s))
- **Nodes**: 7 (0 flow control, 0 data transform, 0 AI components)
- **AI Agents**: 0
- **Credentials**: 1 types
- **Complexity**: 3.6/10
- **Estimated API endpoints**: 1
- **Estimated DB tables**: 3

## Webhook endpoints

- `POST da4071f2-7550-4dae-aa48-8bced4291643` (node: n8n Form Trigger, mode: responseNode)

## Credentials

- `nasaApi`: used by NASA

## Environment variables

- `NASA_API_KEY`

## Data flow

`n8n Form Trigger` → `NASA` → `Respond to Webhook`
