// n8n REST API client — calls the CUSTOMER's n8n instance.
//
// IMPORTANT: This client talks to an n8n instance the customer operates under
// their own licence. We never host n8n. See ADR-001 and ADR-002.

import { z } from "zod";

// --- Zod schemas for n8n API responses ---

export const N8nWorkflowSchema = z.object({
  id: z.string(),
  name: z.string(),
  active: z.boolean(),
  createdAt: z.string(),
  updatedAt: z.string(),
  nodes: z.array(z.any()).optional(),
  connections: z.record(z.any()).optional(),
  settings: z.record(z.any()).optional(),
  tags: z.array(z.object({ id: z.string(), name: z.string() })).optional(),
  staticData: z.any().optional(),
  pinData: z.any().optional(),
  versionId: z.string().optional(),
});

export const N8nExecutionSchema = z.object({
  id: z.string(),
  finished: z.boolean(),
  mode: z.string(),
  retryOf: z.string().nullable().optional(),
  retrySuccessId: z.string().nullable().optional(),
  startedAt: z.string(),
  stoppedAt: z.string().optional(),
  workflowId: z.string(),
  workflowName: z.string().optional(),
  data: z.any().optional(),
  status: z.enum(["success", "error", "waiting", "running", "canceled", "crashed"]).optional(),
});

export const N8nCredentialSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
});

export type N8nWorkflow = z.infer<typeof N8nWorkflowSchema>;
export type N8nExecution = z.infer<typeof N8nExecutionSchema>;
export type N8nCredential = z.infer<typeof N8nCredentialSchema>;

// --- Client ---

export interface N8nClientConfig {
  baseUrl: string;   // customer's n8n URL, e.g. https://n8n.customer.com
  apiKey: string;    // customer's n8n API key
}

export class N8nClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(config: N8nClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/+$/, "");
    this.apiKey = config.apiKey;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}/api/v1${path}`;
    const res = await fetch(url, {
      ...options,
      headers: {
        "X-N8N-API-KEY": this.apiKey,
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!res.ok) {
      const body = await res.text();
      throw new Error(`n8n API ${res.status}: ${body}`);
    }

    return res.json();
  }

  // --- Workflows ---

  async getWorkflows(params?: { active?: boolean; tags?: string[]; limit?: number }): Promise<N8nWorkflow[]> {
    const qs = new URLSearchParams();
    if (params?.active !== undefined) qs.set("active", String(params.active));
    if (params?.tags) qs.set("tags", params.tags.join(","));
    if (params?.limit) qs.set("limit", String(params.limit));
    const data = await this.request<{ data: unknown[] }>(`/workflows?${qs}`);
    return data.data.map((w) => N8nWorkflowSchema.parse(w));
  }

  async getWorkflow(id: string): Promise<N8nWorkflow> {
    const data = await this.request<unknown>(`/workflows/${id}`);
    return N8nWorkflowSchema.parse(data);
  }

  async createWorkflow(workflow: Partial<N8nWorkflow>): Promise<N8nWorkflow> {
    const data = await this.request<unknown>("/workflows", {
      method: "POST",
      body: JSON.stringify(workflow),
    });
    return N8nWorkflowSchema.parse(data);
  }

  async updateWorkflow(id: string, workflow: Partial<N8nWorkflow>): Promise<N8nWorkflow> {
    const data = await this.request<unknown>(`/workflows/${id}`, {
      method: "PUT",
      body: JSON.stringify(workflow),
    });
    return N8nWorkflowSchema.parse(data);
  }

  async deleteWorkflow(id: string): Promise<void> {
    await this.request(`/workflows/${id}`, { method: "DELETE" });
  }

  async activateWorkflow(id: string): Promise<N8nWorkflow> {
    const data = await this.request<unknown>(`/workflows/${id}/activate`, { method: "POST" });
    return N8nWorkflowSchema.parse(data);
  }

  async deactivateWorkflow(id: string): Promise<N8nWorkflow> {
    const data = await this.request<unknown>(`/workflows/${id}/deactivate`, { method: "POST" });
    return N8nWorkflowSchema.parse(data);
  }

  // --- Executions ---

  async getExecutions(params?: {
    workflowId?: string;
    status?: string;
    limit?: number;
    includeData?: boolean;
  }): Promise<N8nExecution[]> {
    const qs = new URLSearchParams();
    if (params?.workflowId) qs.set("workflowId", params.workflowId);
    if (params?.status) qs.set("status", params.status);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.includeData) qs.set("includeData", "true");
    const data = await this.request<{ data: unknown[] }>(`/executions?${qs}`);
    return data.data.map((e) => N8nExecutionSchema.parse(e));
  }

  async getExecution(id: string, includeData = true): Promise<N8nExecution> {
    const qs = includeData ? "?includeData=true" : "";
    const data = await this.request<unknown>(`/executions/${id}${qs}`);
    return N8nExecutionSchema.parse(data);
  }

  async retryExecution(id: string): Promise<N8nExecution> {
    const data = await this.request<unknown>(`/executions/${id}/retry`, { method: "POST" });
    return N8nExecutionSchema.parse(data);
  }

  // --- Credentials ---

  async getCredentials(): Promise<N8nCredential[]> {
    const data = await this.request<{ data: unknown[] }>("/credentials");
    return data.data.map((c) => N8nCredentialSchema.parse(c));
  }

  async createCredential(credential: { name: string; type: string; data: Record<string, unknown> }): Promise<N8nCredential> {
    const data = await this.request<unknown>("/credentials", {
      method: "POST",
      body: JSON.stringify(credential),
    });
    return N8nCredentialSchema.parse(data);
  }

  // --- Health ---

  async healthCheck(): Promise<{ status: string }> {
    try {
      await this.request("/workflows?limit=1");
      return { status: "ok" };
    } catch (e) {
      return { status: "error", error: String(e) } as any;
    }
  }

  // --- Webhooks (trigger workflows) ---

  async triggerWebhook(path: string, data: Record<string, unknown>): Promise<unknown> {
    const url = `${this.baseUrl}/webhook/${path}`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      throw new Error(`Webhook ${res.status}: ${await res.text()}`);
    }
    return res.json();
  }
}

// --- Factory ---

export function createN8nClient(config: N8nClientConfig): N8nClient {
  return new N8nClient(config);
}

// --- Verification ---

export async function verifyConnection(config: N8nClientConfig): Promise<{
  ok: boolean;
  workflowCount?: number;
  error?: string;
}> {
  const client = createN8nClient(config);
  try {
    const workflows = await client.getWorkflows({ limit: 1 });
    return { ok: true, workflowCount: workflows.length };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}