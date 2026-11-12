import { redirect } from "next/navigation";
import Link from "next/link";
import { safeAuth } from "@/lib/auth";

export default async function Home() {
  const { userId } = await safeAuth();
  if (userId) redirect("/dashboard");

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-3xl text-center space-y-6">
        <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
          {"{{WORKFLOW_NAME}}"}
        </h1>
        <p className="text-xl text-muted-foreground">
          Monitor and manage your n8n workflows from a single dashboard.
          Connect your n8n instance, view executions, retry failures, and track usage.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/sign-up"
            className="inline-flex h-11 items-center justify-center rounded-md bg-primary px-8 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Get started
          </Link>
          <Link
            href="/sign-in"
            className="inline-flex h-11 items-center justify-center rounded-md border border-input bg-background px-8 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
          >
            Sign in
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-12 text-left">
          <div className="rounded-lg border p-6">
            <h3 className="font-semibold mb-2">Connect your n8n</h3>
            <p className="text-sm text-muted-foreground">
              Enter your n8n URL and API key. We verify the connection instantly.
            </p>
          </div>
          <div className="rounded-lg border p-6">
            <h3 className="font-semibold mb-2">Monitor executions</h3>
            <p className="text-sm text-muted-foreground">
              View execution history, filter by status, retry failures with one click.
            </p>
          </div>
          <div className="rounded-lg border p-6">
            <h3 className="font-semibold mb-2">Track usage</h3>
            <p className="text-sm text-muted-foreground">
              Execution counts, error rates, and billing — all in one place.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}