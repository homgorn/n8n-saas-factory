import { test, expect } from '@playwright/test';

test.describe('AI Tool SaaS — smoke tests', () => {
  test('landing page loads', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('Chat with Google Sheets');
    await expect(page.locator('a[href="/sign-up"]')).toBeVisible();
  });

  test('auth pages accessible', async ({ page }) => {
    await page.goto('/sign-in');
    await expect(page.locator('h1, h2')).toContainText(/Sign/i);
  });

  test('dashboard redirects when unauthenticated', async ({ page }) => {
    await page.goto('/dashboard');
    // Should redirect to sign-in; the exact URL depends on Clerk config
    await expect(page.url()).toContain('/sign');
  });

  test('n8n webhook endpoint responds with 401 without signature', async ({ request }) => {
    const response = await request.post('/api/webhooks/n8n/test-workflow', {
      data: { workflowId: 'test', executionId: 'test' },
    });
    expect(response.status()).toBe(401);
  });
});
