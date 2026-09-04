import { NextResponse } from "next/server";

import { isBackendAuthResponse } from "@/lib/auth-types";
import {
  copyBackendResponse,
  fetchAuthBackend,
  setSessionCookie,
} from "@/lib/server/auth-backend";
import {
  emitAuthEvent,
  getClientIp,
  getUserAgent,
  takeRateLimit,
  validateSameOrigin,
} from "@/lib/server/request-security";

export async function POST(request: Request): Promise<Response> {
  if (!validateSameOrigin(request)) {
    return NextResponse.json({ detail: "Origin not allowed" }, { status: 403 });
  }

  const clientIp = getClientIp(request);
  const rateLimit = takeRateLimit("login", clientIp, 10);
  if (!rateLimit.allowed) {
    emitAuthEvent("auth_login_rate_limited", {
      outcome: "failure",
      reason: "client_ip_window_exhausted",
      clientIp,
      userAgent: getUserAgent(request),
    });
    return NextResponse.json(
      { detail: "Too many login attempts. Try again later." },
      {
        status: 429,
        headers: { "Retry-After": String(rateLimit.retryAfterSeconds) },
      },
    );
  }

  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json(
      { detail: "Request body must be valid JSON." },
      { status: 400 },
    );
  }

  let response: Response;
  try {
    response = await fetchAuthBackend("/api/auth/login", {
      method: "POST",
      request,
      body: payload,
      includeSession: false,
    });
  } catch {
    return NextResponse.json(
      { detail: "Authentication service is temporarily unavailable." },
      { status: 503 },
    );
  }

  if (!response.ok) return copyBackendResponse(response);

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    return NextResponse.json(
      { detail: "Authentication response was invalid." },
      { status: 502 },
    );
  }
  if (!isBackendAuthResponse(body)) {
    return NextResponse.json(
      { detail: "Authentication response was invalid." },
      { status: 502 },
    );
  }

  const { session_token: sessionToken, ...safeUser } = body;
  void sessionToken;
  const safeResponse = NextResponse.json(safeUser, { status: response.status });
  setSessionCookie(safeResponse, body.session_token);
  return safeResponse;
}
