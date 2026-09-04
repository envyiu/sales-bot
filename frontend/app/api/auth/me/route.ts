import { NextResponse } from "next/server";

import {
  clearSessionCookie,
  copyBackendResponse,
  fetchAuthBackend,
} from "@/lib/server/auth-backend";

export async function GET(request: Request): Promise<Response> {
  let response: Response;
  try {
    response = await fetchAuthBackend("/api/auth/me", {
      method: "GET",
      request,
    });
  } catch {
    return NextResponse.json(
      { detail: "Authentication service is temporarily unavailable." },
      { status: 503 },
    );
  }

  const result = await copyBackendResponse(response);
  if (response.status === 401) clearSessionCookie(result);
  return result;
}
