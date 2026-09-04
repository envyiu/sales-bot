import { fetchAuthBackend } from "@/lib/server/auth-backend";

const backendPath = "/api/chat";

function jsonResponse(body: Record<string, string>, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export async function POST(request: Request): Promise<Response> {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return jsonResponse({ detail: "Request body must be valid JSON." }, 400);
  }

  try {
    const response = await fetchAuthBackend(backendPath, {
      method: "POST",
      request,
      body: payload,
    });

    const headers = new Headers({
      "Content-Type": response.headers.get("content-type") ?? "application/json",
    });
    const retryAfter = response.headers.get("Retry-After");
    if (retryAfter) {
      headers.set("Retry-After", retryAfter);
    }

    return new Response(await response.text(), {
      status: response.status,
      headers,
    });
  } catch {
    return jsonResponse(
      { detail: "Chat backend is temporarily unavailable." },
      503,
    );
  }
}
