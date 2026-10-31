# Workflow Analysis: Tutorial-workflow

**Source**: `n8n-docs-source\docs\_workflows\try-it-out\quickstart\tutorial.json`
**Workflow ID**: `DPzMzTIyDrYohiw4`
**Active**: False

## Summary

- **Trigger**: n8n-nodes-base.scheduleTrigger (1 trigger(s))
- **Nodes**: 6 (1 flow control, 0 data transform, 0 AI components)
- **AI Agents**: 0
- **Credentials**: 1 types
- **Complexity**: 4.6/10
- **Estimated API endpoints**: 1
- **Estimated DB tables**: 3

## Credentials

- `nasaApi`: used by NASA

## Environment variables

- `NASA_API_KEY`

## Data flow

`Schedule Trigger` → `NASA` → `If` → `PostBin(true)` → `PostBin(false)`
