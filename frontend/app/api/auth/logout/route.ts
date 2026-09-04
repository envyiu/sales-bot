import { NextResponse } from "next/server";

import {
  clearSessionCookie,
  copyBackendResponse,
  fetchAuthBackend,
} from "@/lib/server/auth-backend";
import { validateSameOrigin } from "@/lib/server/request-security";

export async function POST(request: Request): Promise<Response> {
  if (!validateSameOrigin(request)) {
    return NextResponse.json({ detail: "Origin not allowed" }, { status: 403 });
  }

  let result: Response;
  try {
    const response = await fetchAuthBackend("/api/auth/logout", {
      method: "POST",
      request,
    });
    result = await copyBackendResponse(response);
  } catch {
    result = NextResponse.json(
      { detail: "Logout completed locally." },
      { status: 503 },
    );
  }

  clearSessionCookie(result);
  return result;
}
