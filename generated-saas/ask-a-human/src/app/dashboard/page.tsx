import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import Link from "next/link";
import { safeAuth, authConfigured } from "@/lib/auth";

export default async function DashboardPage() {
  const { userId } = await safeAuth();
  // Without an auth provider configured there is nothing to sign in to, so the dashboard
  // cannot be reached at all — send the visitor to the landing page instead of erroring.
  if (!authConfigured) redirect("/");
  if (!userId) redirect("/sign-in");

  const supabase = createClient();

  // Get user's tenant
  const { data: user } = await supabase
    .from("users")
    .select("tenant_id, tenants(*)")
    .eq("clerk_id", userId)
    .single();

  if (!user?.tenant_id) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4">No organization found</h1>
        <p className="text-muted-foreground">
          Please create an organization to get started.
        </p>
      </div>
    );
  }

  // Get n8n connections
  const { data: connections } = await supabase
    .from("n8n_connections")
    .select("*")
    .eq("tenant_id", user.tenant_id);

  // Get workflows
  const { data: workflows } = await supabase
    .from("workflows")
    .select("*")
    .eq("tenant_id", user.tenant_id)
    .order("updated_at", { ascending: false });

  // Get recent executions
  const { data: executions } = await supabase
    .from("executions")
    .select("*, workflows(name)")
    .eq("tenant_id", user.tenant_id)
    .order("started_at", { ascending: false })
    .limit(20);

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Link
          href="/dashboard/connect"
          className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Connect n8n
        </Link>
      </div>

      {/* n8n Connections */}
      <section>
        <h2 className="text-xl font-semibold mb-4">n8n Connections</h2>
        {!connections || connections.length === 0 ? (
          <div className="rounded-lg border border-dashed p-8 text-center">
            <p className="text-muted-foreground mb-4">No n8n instance connected yet.</p>
            <Link
              href="/dashboard/connect"
              className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Connect your n8n instance
            </Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {connections.map((conn) => (
              <div key={conn.id} className="rounded-lg border p-4 flex items-center justify-between">
                <div>
                  <p className="font-medium">{conn.name}</p>
                  <p className="text-sm text-muted-foreground">{conn.base_url}</p>
                </div>
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    conn.status === "connected"
                      ? "bg-green-100 text-green-800"
                      : conn.status === "error"
                      ? "bg-red-100 text-red-800"
                      : "bg-yellow-100 text-yellow-800"
                  }`}
                >
                  {conn.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Workflows */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Workflows</h2>
        {!workflows || workflows.length === 0 ? (
          <p className="text-muted-foreground">No workflows synced yet. Connect an n8n instance first.</p>
        ) : (
          <div className="rounded-lg border">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="p-3 text-left text-sm font-medium">Name</th>
                  <th className="p-3 text-left text-sm font-medium">Status</th>
                  <th className="p-3 text-left text-sm font-medium">Nodes</th>
                  <th className="p-3 text-left text-sm font-medium">Last synced</th>
                </tr>
              </thead>
              <tbody>
                {workflows.map((wf) => (
                  <tr key={wf.id} className="border-b">
                    <td className="p-3 text-sm">{wf.name}</td>
                    <td className="p-3 text-sm">
                      <span className={wf.active ? "text-green-600" : "text-muted-foreground"}>
                        {wf.active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="p-3 text-sm">{wf.node_count ?? "—"}</td>
                    <td className="p-3 text-sm text-muted-foreground">
                      {wf.last_synced_at ? new Date(wf.last_synced_at).toLocaleDateString() : "Never"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Recent Executions */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Recent Executions</h2>
        {!executions || executions.length === 0 ? (
          <p className="text-muted-foreground">No executions recorded yet.</p>
        ) : (
          <div className="rounded-lg border">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="p-3 text-left text-sm font-medium">Workflow</th>
                  <th className="p-3 text-left text-sm font-medium">Status</th>
                  <th className="p-3 text-left text-sm font-medium">Started</th>
                  <th className="p-3 text-left text-sm font-medium">Duration</th>
                </tr>
              </thead>
              <tbody>
                {executions.map((exec) => (
                  <tr key={exec.id} className="border-b">
                    <td className="p-3 text-sm">{(exec as any).workflows?.name ?? "Unknown"}</td>
                    <td className="p-3 text-sm">
                      <span
                        className={
                          exec.status === "success"
                            ? "text-green-600"
                            : exec.status === "error"
                            ? "text-red-600"
                            : "text-muted-foreground"
                        }
                      >
                        {exec.status}
                      </span>
                    </td>
                    <td className="p-3 text-sm text-muted-foreground">
                      {new Date(exec.started_at).toLocaleString()}
                    </td>
                    <td className="p-3 text-sm text-muted-foreground">
                      {exec.duration_ms ? `${exec.duration_ms}ms` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}