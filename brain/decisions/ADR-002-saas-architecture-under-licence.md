# ADR-002: SaaS architecture under the n8n licence constraint

- **Status**: Accepted
- **Date**: 2026-10-31
- **Deciders**: owner, with deep-research on 2026-10-31
- **Claim type**: mixed — `reported` for third-party sources, `inferred` for the architecture conclusion, `measured` for the corpus counts

## Context

ADR-001 established the constraint: n8n is under the Sustainable Use License, which does not permit
providing n8n to third parties for profit. The question this ADR answers is: **given that constraint,
what is the product and what does it actually ship?**

## Decision

**The product is a SaaS dashboard that drives a customer's own n8n instance. n8n is never hosted,
embedded, or redistributed by us.**

Three paths were evaluated:

| Path | Cost | Legal position | Verdict |
| --- | --- | --- | --- |
| **OEM / Embed** (n8n's paid programme) | ~$50,000/year reported | Licenced | Rejected as premature — a sales conversation, not a code task. Revisit when a customer needs zero-setup onboarding. |
| **Host n8n ourselves** | ~$0 (we already have the infra) | **Not licenced.** Automatic and permanent termination on violation. | Rejected — permanent termination is not a risk to take. |
| **Customer brings their own n8n** | $0 | Permitted. Each party uses n8n under its own licence; we are not distributing it. | **Accepted.** |

[reported: Activepieces blog, 2026-10-31 — OEM embed agreement ~$50,000/yr]
[reported: n8n community forum, 2026-10-31 — commercial license inquiries point at the same figure]
[reported: n8n Sustainable Use License, 2026-10-12 — "You may use or modify the software only for your own internal business purposes or for non-commercial or personal use."]

## What the product actually does

1. **Onboarding**: the customer enters `N8N_BASE_URL` and an API key (or completes an OAuth2 token exchange).
2. **Dashboard**: we call the customer's n8n REST API (`/api/v1/workflows`, `/api/v1/executions`) and show:
   - workflow list with active/inactive status
   - execution history with filtering by workflow, status, date
   - execution detail: input data, output data, error stack
   - retry failed executions
   - trigger test executions
3. **Multi-tenancy**: each tenant row stores a reference to a customer's n8n instance, never the instance itself. Credentials live in the customer's vault; we hold a reference key.
4. **Billing**: Stripe subscription per tenant. Usage metering comes from the customer's n8n execution count, which we read via API.
5. **Workflow templates**: we ship pre-built workflow JSON (from `brain/data/wiki.db` `workflows` table, 12 examples) that the customer imports into *their* n8n with one click.
6. **Observability**: aggregate execution stats across tenants, error rates, latency — all read from the customer's API.

## What the product does NOT do

- Host, embed (iframe), or redistribute n8n.
- Store n8n credentials in our database — only a reference token.
- Execute workflows on our infrastructure.
- Offer "zero-setup" onboarding — the customer must have n8n running first.

## Verification

Before any generated SaaS ships:

- [ ] Every `.env.example` documents `N8N_BASE_URL` as the customer's instance.
- [ ] No n8n server image in our `docker-compose.yml`.
- [ ] No n8n credentials table in our schema — only `tenant_n8n_reference` with URL + encrypted API key ref.
- [ ] README states the licence position.
- [ ] A customer can disconnect their n8n and all our features degrade gracefully (no crash, clear error).
- [ ] The onboarding flow explicitly asks: "Do you have an n8n instance running?" with a link to n8n's install docs.

## Alternatives rejected

1. **Wait for OEM pricing to drop.** Rejected: the architecture works without it; OEM is a future option.
2. **Build our own workflow engine.** Rejected: the 500-node integration library is the product; reimplementing it is a company, not a feature.
3. **Hide n8n behind our brand ("white-label").** Rejected: this is exactly what the licence forbids.

## Consequences

Good:
- No n8n instance to operate, patch, or pay for.
- Credentials stay on the customer's side — we never hold their n8n API key in plaintext.
- The product's value is the dashboard, billing, and multi-tenancy layer — defensible and licensable.
- We can ship today without a commercial conversation with n8n.

Bad:
- **No "one-click, no-setup" pitch.** Customer must have n8n running first. Onboarding is heavier.
- **Weaker moat.** The workflow engine is not ours; a competitor could build the same layer.
- **Revenue ceiling.** We cannot charge for the automation itself, only for the SaaS layer.

## Confidence

- Licence reading: 9/10 (direct quote from authoritative source).
- OEM cost figure: 5/10 (reported by third parties, not confirmed by n8n pricing page).
- Architecture viability: 8/10 (the customer-brings-n8n pattern is well-documented in the n8n community).

## Sources

- [reported] n8n Sustainable Use License, https://github.com/n8n-io/n8n/blob/master/LICENSE.md, retrieved 2026-10-12
- [reported] Activepieces blog, "n8n White Label: Cost and What You Can Rebrand", https://www.activepieces.com/blog/n8n-white-label-cost-and-what-you-can-rebrand-2026, retrieved 2026-10-31
- [reported] n8n community forum, "Does anyone have a rough idea of how much an n8n commercial license would cost", https://community.n8n.io/t/does-anyone-have-a-rough-idea-of-how-much-an-n8n-commercial-license-would-cost-to-integrate-n8n-into-a-b2b-saas-solution-that-we-sell-to-businesses/316047, retrieved 2026-10-31
- [reported] n8n docs, "Deploy as an OEM integration", https://docs.n8n.io/deploy/host-n8n/deploy-as-an-oem-integration, retrieved 2026-10-31
- [reported] Siennabase multi-tenant boilerplate, https://community.n8n.io/t/built-a-multi-tenant-boilerplate-for-running-n8n-across-many-client-instances-siennabase/301807, retrieved 2026-10-31
- [reported] five.co, "Dynamic Credential Management in n8n", https://five.co/blog/n8n-dynamic-credential-management/, retrieved 2026-10-31
- [reported] wednesday.is, "Building Multi-Tenant n8n Workflows for Agency Clients", https://www.wednesday.is/writing-articles/building-multi-tenant-n8n-workflows-for-agency-clients/, retrieved 2026-10-31