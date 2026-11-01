{
  "scheduled": {
    "F008": "n8n sync workflows requires a running n8n instance for webhook/cron verification"
  },
  "unresolved_hypotheses": [
    "Can the customer bring their own n8n Cloud account without violating the Sustainable Use License? (ADR-002, unconfirmed claim)",
    "What is the exact annual cost of the n8n OEM / embed agreement? (ADR-002, reported claim — $50k from third-party sources, unconfirmed by n8n pricing)"
  ],
  "next_refresh": [
    "Check n8n docs llms-full.txt for new pages or updated node documentation",
    "Refresh claims: verify the OEM price figure, confirm customer-brings-own-instance legal position",
    "Refresh vector DB: once OPENAI_API_KEY is set, rebuild embeddings for new chunks"
  ],
  "stale_triggers": {
    "n8n_docs_changed": "Compare sitemap.md with previous index; delta in refresh-logs/",
    "n8n_version_changed": "Read changelog/readme.md for new releases",
    "new_workflow_templates": "Check docs/_workflows/ and docs/_workflows/advanced-ai/",
    "new_nodes": "Compare node count and types in integrations/builtin/core-nodes/",
    "oem_price_updated": "Check activepieces.com / community.n8n.io / n8n docs deploy section"
  }
}