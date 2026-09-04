export interface AuthUser {
  id: string;
  email: string;
  display_name: string | null;
  created_at: string;
  session_expires_at: string;
}

export interface BackendAuthResponse extends AuthUser {
  session_token: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function isAuthUser(value: unknown): value is AuthUser {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    typeof value.email === "string" &&
    (value.display_name === null || typeof value.display_name === "string") &&
    typeof value.created_at === "string" &&
    typeof value.session_expires_at === "string"
  );
}

export function isBackendAuthResponse(
  value: unknown,
): value is BackendAuthResponse {
  return (
    isAuthUser(value) &&
    typeof (value as unknown as Record<string, unknown>).session_token === "string"
  );
}

export function responseDetail(value: unknown): string | undefined {
  if (!isRecord(value)) return undefined;
  if (typeof value.detail === "string") return value.detail;
  if (Array.isArray(value.detail)) {
    const firstError = value.detail.find((item) => isRecord(item));
    if (firstError && typeof firstError.msg === "string") {
      return firstError.msg;
    }
  }
  return undefined;
}
