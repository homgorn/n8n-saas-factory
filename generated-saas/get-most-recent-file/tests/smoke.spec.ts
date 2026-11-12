import { test, expect } from "@playwright/test";

/**
 * Smoke tests for the AI Tool SaaS template.
 *
 * They run against a real Next.js dev server (started by playwright.config.ts), not
 * against a mock. A test that cannot be run is worse than no test: it looks like
 * coverage while measuring nothing.
 */

test.describe("AI Tool SaaS — smoke tests", () => {
  test("landing page loads", async ({ page }) => {
    const response = await page.goto("/");
    expect(response?.status()).toBeLessThan(400);
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.locator("h1")).not.toHaveText("");
    await expect(page.getByRole("link", { name: /get started/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /sign in/i })).toBeVisible();
  });

  test("the workflow name reaches the page", async ({ page }) => {
    // In a generated project the heading is the workflow name; in the template it is the
    // Get most recent file placeholder. Both must render as text, never as an empty element.
    await page.goto("/");
    const heading = (await page.locator("h1").innerText()).trim();
    expect(heading.length).toBeGreaterThan(0);
    expect(heading).not.toContain("undefined");
  });

  test("dashboard is not reachable without a session", async ({ page }) => {
    await page.goto("/dashboard");
    // Unauthenticated visitors must not see the dashboard. Depending on the auth provider
    // the app either redirects or renders a sign-in wall; both are acceptable, an empty
    // dashboard is not.
    const url = page.url();
    const body = (await page.locator("body").innerText()).toLowerCase();
    const redirected = !url.endsWith("/dashboard");
    const showsSignIn = body.includes("sign in") || body.includes("sign up") || body.includes("log in");
    expect(redirected || showsSignIn).toBe(true);
  });

  test("n8n webhook endpoint rejects an unsigned request", async ({ request }) => {
    const response = await request.post("/api/webhooks/n8n", {
      data: { workflowId: "test", executionId: "test" },
    });
    expect(response.status()).toBe(401);
  });

  test("n8n webhook endpoint rejects a malformed signature", async ({ request }) => {
    const response = await request.post("/api/webhooks/n8n", {
      headers: { "x-n8n-signature": "not-a-valid-hmac" },
      data: { workflowId: "test", executionId: "test" },
    });
    expect(response.status()).toBe(401);
  });
});
