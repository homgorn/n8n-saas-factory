import { auth } from "@clerk/nextjs/server";

/**
 * Auth access that does not explode when the auth provider is not configured.
 *
 * The template must run locally without secrets: `npm run dev` and the smoke tests have
 * to work before anyone has a Clerk account. `auth()` throws when the publishable key is
 * missing, which turned a missing key into a 500 on every page.
 */
export const authConfigured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

export async function safeAuth(): Promise<{ userId: string | null }> {
  if (!authConfigured) return { userId: null };
  try {
    const session = await auth();
    return { userId: session.userId };
  } catch {
    return { userId: null };
  }
}
