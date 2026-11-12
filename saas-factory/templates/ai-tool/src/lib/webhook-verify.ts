import crypto from "crypto";

/**
 * Webhook signature check. Fails closed.
 *
 * When no shared secret is configured the request is rejected, not accepted: a webhook
 * that accepts unsigned payloads in development and rejects them in production is how
 * unsigned writes reach a database. Opt in to a local shortcut explicitly with
 * N8N_WEBHOOK_SECRET=dev.
 */
export function verifyWebhookSignature(
  body: string,
  signature: string | null
): boolean {
  const secret = process.env.N8N_WEBHOOK_SECRET;

  if (!secret) {
    if (process.env.N8N_WEBHOOK_ALLOW_UNSIGNED === "true") {
      console.warn(
        "n8n webhook accepted without a signature (N8N_WEBHOOK_ALLOW_UNSIGNED=true)"
      );
      return true;
    }
    console.warn(
      "n8n webhook rejected: N8N_WEBHOOK_SECRET is not set. Set it, or set " +
        "N8N_WEBHOOK_ALLOW_UNSIGNED=true for local development."
    );
    return false;
  }

  if (!signature) return false;

  const expected = crypto
    .createHmac("sha256", secret)
    .update(body)
    .digest("hex");

  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expected)
    );
  } catch {
    return false;
  }
}
