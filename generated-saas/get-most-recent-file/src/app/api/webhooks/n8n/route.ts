import { NextRequest, NextResponse } from "next/server";
import { verifyWebhookSignature } from "@/lib/webhook-verify";
import { createClient } from "@/lib/supabase/server";
import { z } from "zod";

const WebhookPayloadSchema = z.object({
  workflowId: z.string(),
  executionId: z.string(),
  status: z.enum(["success", "error", "waiting", "running", "canceled", "crashed"]),
  startedAt: z.string(),
  stoppedAt: z.string().optional(),
  mode: z.string().optional(),
  data: z.any().optional(),
  error: z.object({ message: z.string(), stack: z.string().optional() }).optional(),
});

export async function POST(request: NextRequest) {
  const signature = request.headers.get("x-n8n-signature");
  const body = await request.text();

  // Verify webhook signature (HMAC-SHA256 with shared secret)
  if (!verifyWebhookSignature(body, signature)) {
    return NextResponse.json({ error: "Invalid signature" }, { status: 401 });
  }

  let payload: z.infer<typeof WebhookPayloadSchema>;
  try {
    payload = WebhookPayloadSchema.parse(JSON.parse(body));
  } catch (e) {
    return NextResponse.json({ error: "Invalid payload", details: e }, { status: 400 });
  }

  const supabase = createClient();

  // Find the workflow by n8n workflow ID
  const { data: workflow, error: wfError } = await supabase
    .from("workflows")
    .select("id, tenant_id")
    .eq("n8n_workflow_id", payload.workflowId)
    .single();

  if (wfError || !workflow) {
    return NextResponse.json({ error: "Workflow not found" }, { status: 404 });
  }

  // Upsert execution record
  const { error: execError } = await supabase.from("executions").upsert(
    {
      tenant_id: workflow.tenant_id,
      workflow_id: workflow.id,
      n8n_execution_id: payload.executionId,
      status: payload.status,
      mode: payload.mode,
      started_at: payload.startedAt,
      stopped_at: payload.stoppedAt,
      duration_ms: payload.stoppedAt
        ? new Date(payload.stoppedAt).getTime() - new Date(payload.startedAt).getTime()
        : null,
      error_message: payload.error?.message,
      input_data: payload.data?.input || null,
      output_data: payload.data?.output || null,
    },
    { onConflict: "workflow_id,n8n_execution_id" }
  );

  if (execError) {
    console.error("Failed to upsert execution:", execError);
    return NextResponse.json({ error: "Database error" }, { status: 500 });
  }

  // Update usage record for billing
  const periodStart = new Date(payload.startedAt);
  periodStart.setDate(1);
  periodStart.setHours(0, 0, 0, 0);

  await supabase.rpc("increment_usage", {
    p_tenant_id: workflow.tenant_id,
    p_period_start: periodStart.toISOString(),
    p_execution_count: 1,
  });

  return NextResponse.json({ ok: true, executionId: payload.executionId });
}