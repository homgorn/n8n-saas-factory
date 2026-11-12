import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dynamic credentials using expressions — SaaS Dashboard",
  description: "Monitor and manage your n8n workflows from a single dashboard.",
};

/**
 * The auth provider is only mounted when it is configured. Without a Clerk key the app
 * still boots and renders, which is what makes local development and the smoke tests
 * possible before any secrets exist.
 */
export default function RootLayout({ children }: { children: React.ReactNode }) {
  const body = (
    <html lang="en">
      <body className="min-h-screen bg-background font-sans antialiased">
        {children}
      </body>
    </html>
  );

  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
    return body;
  }

  return (
    <ClerkProvider>
      <html lang="en">
        <body className="min-h-screen bg-background font-sans antialiased">
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
