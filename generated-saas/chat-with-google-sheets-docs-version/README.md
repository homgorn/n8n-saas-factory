# chat-with-google-sheets-docs-version

SaaS dashboard for n8n workflows. Built from workflow: **Chat with Google Sheets (docs version)**.

> **Licence note**: This product calls a n8n instance that the customer operates
> under their own licence. We do not host, embed, or redistribute n8n.
> See `brain/decisions/ADR-001-n8n-licence-blocks-hosted-saas.md`.

## Quick start

1. **Prerequisites**: Node.js 20+, a Supabase project, a Clerk app, a Stripe account,
   and a running n8n instance (the customer's).

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Fill in all values, especially N8N_BASE_URL and N8N_API_KEY
   ```

4. **Run database migrations**:
   ```bash
   npx supabase db push
   ```

5. **Start development server**:
   ```bash
   npm run dev
   ```

6. **Open**: http://localhost:3000

## Architecture

```
Customer's n8n instance  <--REST API-->  Our SaaS (Next.js)
     (their licence)                           (our product)
```

- **Auth**: Clerk (organizations + RBAC)
- **Database**: Supabase (Postgres + RLS)
- **Billing**: Stripe (subscription webhooks)
- **n8n integration**: REST API client (customer's instance)

## Workflow details

- **Name**: Chat with Google Sheets (docs version)
- **Trigger**: n8n-nodes-base.executeWorkflowTrigger (2 trigger(s))
- **Nodes**: 23
- **AI Agents**: 1
- **Credentials**: none
- **Complexity**: 9/10
- **Estimated API endpoints**: 2
- **Estimated DB tables**: 3

## Deployment

### Vercel (recommended for frontend)

```bash
vercel deploy --prod
```

### Environment variables

Set all variables from `.env.example` in your Vercel project settings.

### Customer onboarding

1. Customer signs up → creates organization
2. Customer enters their n8n URL and API key
3. We verify the connection (health check)
4. Customer imports workflow templates (one-click)
5. Dashboard shows workflows, executions, billing

## License

This project's code: MIT (see LICENSE).
n8n documentation and workflows: Sustainable Use License (n8n GmbH).
