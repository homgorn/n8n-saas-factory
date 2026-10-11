# ADR-001: n8n licence blocks the default SaaS architecture

- **Status**: Accepted, architecture changed
- **Date**: 2026-10-12
- **Deciders**: owner
- **Claim type**: `reported` — https://github.com/n8n-io/n8n/blob/master/LICENSE.md, retrieved 2026-10-12

## Context

The project's stated goal: *«создание саас из ворклофу н8н»* — build a SaaS product out of n8n
workflows. The plan written before this ADR assumed a Next.js frontend calling an n8n webhook, with
n8n deployed for us in the same stack.

## The constraint

n8n is **not** MIT. It ships under the Sustainable Use License. The operative clause:

> You may use or modify the software only for your own **internal business purposes** or for
> **non-commercial or personal use**. You may distribute the software or provide it to others
> **only if you do so free of charge for non-commercial purposes**.

[reported, 2026-10-12]

Consequences for the two architectures that were on the table:

| architecture | verdict |
| --- | --- |
| We host one n8n instance; our SaaS calls it; paying customers get the workflow results | **Not licensed.** We are providing n8n-derived functionality to third parties for profit. |
| We embed n8n (OEM / iframe) into our dashboard; paying customers drive it | **Not licensed without a separate agreement.** |

A third, different architecture is unaffected:

| architecture | verdict |
| --- | --- |
| Our SaaS calls a **customer's own** n8n instance through the public REST API, authenticated with a key the customer supplies | Permitted. Each party uses n8n under its own licence; we are not distributing n8n. |

## Decision

**The default architecture becomes: each customer brings their own n8n.**

Our product is the layer above the workflow engine — the dashboard, the billing, the API surface,
the multi-tenant plumbing, the observability. n8n is the customer's execution runtime, reached
over `POST /webhook/...` or the public REST API with their credentials.

For customers who cannot self-host, the commercial path is n8n's **OEM integration programme**
(`https://docs.n8n.io/host-n8n/deploy-as-an-oem-integration`), which is a paid licence and a separate
commercial relationship. That is a business-development task, not a code task, and it is not
assumed.

## Consequences

Good — these become harder but real:

- No n8n instance in our own infrastructure to operate, patch, or pay for.
- Credential handling stays entirely on the customer's side. We never hold their n8n API key in
  our database; we store a reference to it and the key lives in their vault.
- The multi-tenancy problem becomes URL routing rather than instance isolation.
- Our SaaS value is the product surface, not the automation engine. That is a real business, and
  it is the only one the licence permits without a separate deal.

Bad — these are genuine costs:

- **Losing the "one-click, no-setup" pitch.** A customer without n8n cannot start. The landing page
  cannot claim zero setup.
- **Onboarding is heavier.** We need a clear "connect your n8n" flow and error states for a
  customer whose instance is unreachable.
- **Weaker moat.** The workflow engine is not ours; a competitor could build the same layer.

## Alternatives rejected

1. **Buy an n8n Enterprise licence up front.** Rejected as premature — it is a sales conversation
   and a cost, and the architecture works without it. Revisit when a customer actually needs it.
2. **Reimplement the engine.** The value of a workflow product is the 500-node integration library.
   Reimplementing it is not a project, it is a company.
3. **Ship under the licence and hope.** Not an option: the termination clause is automatic and
   permanent on violation, including after reinstatement.

## Verification

Before any generated SaaS ships, confirm which n8n it talks to and under whose licence:

- [ ] Every `.env.example` documents whether `N8N_BASE_URL` is the customer's instance or ours.
- [ ] No n8n server image in our own `docker-compose.yml`.
- [ ] No n8n credentials table in our schema — only a customer-supplied reference.
- [ ] README states the licence position rather than implying n8n is ours to distribute.

**Confidence: 9/10** on the licence reading (direct quote from the authoritative file, retrieved and
read in full). **Unresolved**: whether a customer running n8n Cloud and connecting to us via webhook
counts as "providing to others" under the licence. That reading needs a lawyer, not a README.