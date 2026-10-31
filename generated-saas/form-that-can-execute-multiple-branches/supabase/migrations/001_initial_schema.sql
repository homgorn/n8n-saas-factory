-- Migration: 001_initial_schema.sql
-- SaaS template: customer brings their own n8n instance.
-- We never host n8n. See ADR-001 and ADR-002.

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tenants (organizations)
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  plan TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'starter', 'pro', 'enterprise')),
  stripe_customer_id TEXT,
  stripe_subscription_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Users (linked to Clerk)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  clerk_id TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  name TEXT,
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- n8n instance connections (customer's instance, NOT ours)
CREATE TABLE n8n_connections (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  base_url TEXT NOT NULL,
  api_key_encrypted TEXT NOT NULL,  -- encrypted at rest, never plaintext
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'connected', 'error', 'disconnected')),
  last_health_check TIMESTAMPTZ,
  last_error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(tenant_id, base_url)
);

-- Workflows (mirrored from customer's n8n instance)
CREATE TABLE workflows (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  n8n_connection_id UUID NOT NULL REFERENCES n8n_connections(id) ON DELETE CASCADE,
  n8n_workflow_id TEXT NOT NULL,
  name TEXT NOT NULL,
  active BOOLEAN NOT NULL DEFAULT FALSE,
  node_count INTEGER,
  trigger_type TEXT,
  last_synced_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(n8n_connection_id, n8n_workflow_id)
);

-- Executions (mirrored from customer's n8n instance)
CREATE TABLE executions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  n8n_execution_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('success', 'error', 'waiting', 'running', 'canceled', 'crashed')),
  mode TEXT,
  started_at TIMESTAMPTZ NOT NULL,
  stopped_at TIMESTAMPTZ,
  duration_ms INTEGER,
  error_message TEXT,
  input_data JSONB,
  output_data JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(workflow_id, n8n_execution_id)
);

-- API keys (for our SaaS API, not n8n's)
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  key_hash TEXT NOT NULL,  -- bcrypt hash of the key
  key_prefix TEXT NOT NULL,  -- first 8 chars for display
  last_used_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  revoked_at TIMESTAMPTZ
);

-- Usage tracking (for billing metering)
CREATE TABLE usage_records (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  period_start TIMESTAMPTZ NOT NULL,
  period_end TIMESTAMPTZ NOT NULL,
  execution_count INTEGER NOT NULL DEFAULT 0,
  api_call_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(tenant_id, period_start)
);

-- Indexes
CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_clerk ON users(clerk_id);
CREATE INDEX idx_n8n_connections_tenant ON n8n_connections(tenant_id);
CREATE INDEX idx_workflows_tenant ON workflows(tenant_id);
CREATE INDEX idx_workflows_connection ON workflows(n8n_connection_id);
CREATE INDEX idx_executions_tenant ON executions(tenant_id);
CREATE INDEX idx_executions_workflow ON executions(workflow_id);
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_executions_started ON executions(started_at DESC);
CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id);
CREATE INDEX idx_usage_tenant_period ON usage_records(tenant_id, period_start DESC);

-- Row Level Security (Supabase)
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE n8n_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_records ENABLE ROW LEVEL SECURITY;

-- RLS policies: users can only see their own tenant's data
CREATE POLICY "tenant_isolation" ON tenants
  FOR ALL USING (id IN (SELECT tenant_id FROM users WHERE clerk_id = auth.uid()::text));

CREATE POLICY "tenant_isolation" ON users
  FOR ALL USING (tenant_id IN (SELECT tenant_id FROM users WHERE clerk_id = auth.uid()::text));

CREATE POLICY "tenant_isolation" ON n8n_connections
  FOR ALL USING (tenant_id IN (SELECT tenant_id FROM users WHERE clerk_id = auth.uid()::text));

CREATE POLICY "tenant_isolation" ON workflows
  FOR ALL USING (tenant_id IN (SELECT tenant_id FROM users WHERE clerk_id = auth.uid()::text));

CREATE POLICY "tenant_isolation" ON executions
  FOR ALL USING (tenant_id IN (SELECT tenant_id FROM users WHERE clerk_id = auth.uid()::text));

CREATE POLICY "tenant_isolation" ON api_keys
  FOR ALL USING (tenant_id IN (SELECT tenant_id FROM users WHERE clerk_id = auth.uid()::text));

CREATE POLICY "tenant_isolation" ON usage_records
  FOR ALL USING (tenant_id IN (SELECT tenant_id FROM users WHERE clerk_id = auth.uid()::text));

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tenants_updated_at BEFORE UPDATE ON tenants
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER users_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER n8n_connections_updated_at BEFORE UPDATE ON n8n_connections
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER workflows_updated_at BEFORE UPDATE ON workflows
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();