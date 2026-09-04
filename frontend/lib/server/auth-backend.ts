import "server-only";

import { cookies } from "next/headers";

import {
  getClientIp,
  getUserAgent,
} from "@/lib/server/request-security";

export const AUTH_COOKIE_NAME = "sales_bot_session";

function backendUrl(): string | undefined {
  return process.env.BACKEND_API_URL;
}

function sessionTtlSeconds(): number {
  const configured = Number(process.env.AUTH_SESSION_TTL_SECONDS);
  return Number.isInteger(configured) && configured > 0 ? configured : 86_400;
}

function cookieSecure(): boolean {
  return process.env.AUTH_COOKIE_SECURE === "true";
}

export async function fetchAuthBackend(
  path: string,
  options: {
    request: Request;
    method: "GET" | "POST";
    body?: unknown;
    includeSession?: boolean;
  },
): Promise<Response> {
  const configuredBackendUrl = backendUrl();
  if (!configuredBackendUrl) {
    throw new Error("BACKEND_API_URL is not configured");
  }

  const headers = new Headers();
  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  if (options.includeSession !== false) {
    const cookieStore = await cookies();
    const token = cookieStore.get(AUTH_COOKIE_NAME)?.value;
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const clientIp = getClientIp(options.request);
  if (clientIp !== "unknown") headers.set("X-Auth-Client-IP", clientIp);
  const userAgent = getUserAgent(options.request);
  if (userAgent) headers.set("User-Agent", userAgent);

  return fetch(`${configuredBackendUrl.replace(/\/$/, "")}${path}`, {
    method: options.method,
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    cache: "no-store",
  });
}

export function copyBackendResponse(response: Response): Promise<Response> {
  const headers = new Headers({
    "Content-Type": response.headers.get("content-type") ?? "application/json",
  });
  const retryAfter = response.headers.get("Retry-After");
  if (retryAfter) headers.set("Retry-After", retryAfter);

  return response.text().then(
    (body) => new Response(body, { status: response.status, headers }),
  );
}

export function setSessionCookie(response: Response, token: string): void {
  if (!(response instanceof Response)) return;
  const cookieStore = response.headers;
  const cookie = [
    `${AUTH_COOKIE_NAME}=${encodeURIComponent(token)}`,
    "Path=/",
    "HttpOnly",
    "SameSite=Lax",
    `Max-Age=${sessionTtlSeconds()}`,
  ];
  if (cookieSecure()) cookie.push("Secure");
  cookieStore.append("Set-Cookie", cookie.join("; "));
}

export function clearSessionCookie(response: Response): void {
  if (!(response instanceof Response)) return;
  const cookie = [
    `${AUTH_COOKIE_NAME}=`,
    "Path=/",
    "HttpOnly",
    "SameSite=Lax",
    "Max-Age=0",
  ];
  if (cookieSecure()) cookie.push("Secure");
  response.headers.append("Set-Cookie", cookie.join("; "));
}
