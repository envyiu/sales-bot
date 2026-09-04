import {
  isAuthUser,
  responseDetail,
  type AuthUser,
} from "@/lib/auth-types";

export class AuthApiError extends Error {
  readonly status: number;
  readonly retryAfter?: number;

  constructor(message: string, status: number, retryAfter?: number) {
    super(message);
    this.name = "AuthApiError";
    this.status = status;
    this.retryAfter = retryAfter;
  }
}

function retryAfterSeconds(response: Response): number | undefined {
  const value = Number(response.headers.get("Retry-After"));
  return Number.isFinite(value) && value > 0 ? Math.ceil(value) : undefined;
}

export async function authenticate(
  mode: "login" | "register",
  payload: Record<string, string>,
): Promise<AuthUser> {
  let response: Response;
  try {
    response = await fetch(`/api/auth/${mode}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new AuthApiError("The authentication service is unavailable.", 0);
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    body = undefined;
  }

  if (!response.ok) {
    throw new AuthApiError(
      responseDetail(body) || "Authentication could not be completed.",
      response.status,
      retryAfterSeconds(response),
    );
  }
  if (!isAuthUser(body)) {
    throw new AuthApiError("The authentication response was invalid.", response.status);
  }
  return body;
}

export async function getCurrentUser(): Promise<AuthUser | null> {
  const response = await fetch("/api/auth/me", { cache: "no-store" });
  if (response.status === 401) return null;
  if (!response.ok) {
    throw new AuthApiError("Could not load your account.", response.status);
  }
  const body: unknown = await response.json();
  return isAuthUser(body) ? body : null;
}
