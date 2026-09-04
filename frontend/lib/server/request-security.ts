import "server-only";

const RATE_LIMIT_WINDOW_MS = 60_000;

interface RateLimitBucket {
  timestamps: number[];
}

export interface RateLimitResult {
  allowed: boolean;
  retryAfterSeconds: number;
}

const buckets = new Map<string, RateLimitBucket>();

export function validateSameOrigin(request: Request): boolean {
  const origin = request.headers.get("origin");
  if (!origin) return true;

  const requestUrl = new URL(request.url);
  const protocol =
    request.headers.get("x-forwarded-proto")?.split(",")[0]?.trim() ||
    requestUrl.protocol.replace(":", "");
  const host =
    request.headers.get("host") ||
    request.headers.get("x-forwarded-host")?.split(",")[0]?.trim() ||
    requestUrl.host;

  try {
    return new URL(origin).origin === new URL(`${protocol}://${host}`).origin;
  } catch {
    return false;
  }
}

export function getClientIp(request: Request): string {
  const cloudflareIp = request.headers.get("cf-connecting-ip")?.trim();
  if (cloudflareIp) return cloudflareIp;

  const forwardedFor = request.headers.get("x-forwarded-for");
  const firstForwardedIp = forwardedFor?.split(",")[0]?.trim();
  if (firstForwardedIp) return firstForwardedIp;

  const realIp = request.headers.get("x-real-ip")?.trim();
  return realIp || "unknown";
}

export function getUserAgent(request: Request): string | undefined {
  const userAgent = request.headers.get("user-agent")?.trim();
  return userAgent ? userAgent.slice(0, 512) : undefined;
}

export function takeRateLimit(
  scope: string,
  clientIp: string,
  limit: number,
  now = Date.now(),
): RateLimitResult {
  const key = `${scope}:${clientIp}`;
  const bucket = buckets.get(key) ?? { timestamps: [] };
  bucket.timestamps = bucket.timestamps.filter(
    (timestamp) => now - timestamp < RATE_LIMIT_WINDOW_MS,
  );

  if (bucket.timestamps.length >= limit) {
    const oldest = bucket.timestamps[0] ?? now;
    const retryAfterSeconds = Math.max(
      1,
      Math.ceil((oldest + RATE_LIMIT_WINDOW_MS - now) / 1000),
    );
    buckets.set(key, bucket);
    return { allowed: false, retryAfterSeconds };
  }

  bucket.timestamps.push(now);
  buckets.set(key, bucket);
  return { allowed: true, retryAfterSeconds: 0 };
}

export function emitAuthEvent(
  event: string,
  fields: {
    outcome: string;
    reason?: string;
    clientIp?: string;
    userAgent?: string;
  },
): void {
  console.info(
    JSON.stringify({
      event,
      ...fields,
      created_at: new Date().toISOString(),
    }),
  );
}
