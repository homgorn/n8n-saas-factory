import crypto from "crypto";

export function verifyWebhookSignature(
  body: string,
  signature: string | null
): boolean {
  if (!signature) return false;

  const secret = process.env.N8N_WEBHOOK_SECRET;
  if (!secret) {
    console.warn("N8N_WEBHOOK_SECRET not set — skipping verification (dev only)");
    return process.env.NODE_ENV === "development";
  }

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