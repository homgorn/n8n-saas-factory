import { defineConfig, devices } from "@playwright/test";

const PORT = process.env.SMOKE_PORT || "3210";
const baseURL = process.env.SMOKE_BASE_URL || `http://127.0.0.1:${PORT}`;

/**
 * Smoke tests run against a real Next.js dev server started by Playwright itself
 * (webServer below). No Vercel, no deployment, no credentials needed for the parts of
 * the app that do not require an auth provider.
 */
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30_000,
  reporter: [["list"]],
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: `npm run dev -- --port ${PORT}`,
    url: baseURL,
    reuseExistingServer: true,
    timeout: 120_000,
    env: {
      NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || "",
      CLERK_SECRET_KEY: process.env.CLERK_SECRET_KEY || "",
    },
  },
});
