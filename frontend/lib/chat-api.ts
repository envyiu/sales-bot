import type { ChatProduct, ChatResponse } from "@/lib/chat-types";

interface SendChatMessageInput {
  conversationId?: string | null;
  message: string;
}

export class ChatApiError extends Error {
  readonly status: number;
  readonly retryAfter?: number;

  constructor(message: string, status: number, retryAfter?: number) {
    super(message);
    this.name = "ChatApiError";
    this.status = status;
    this.retryAfter = retryAfter;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

function isChatProduct(value: unknown): value is ChatProduct {
  if (!isRecord(value)) return false;

  const numberFields = [
    "id",
    "price_vnd",
    "ram_gb",
    "storage_gb",
    "battery_mah",
    "gaming_score",
    "camera_score",
    "battery_score",
    "performance_score",
    "display_score",
    "stock_quantity",
  ];
  const stringFields = ["slug", "name", "brand", "model", "chipset"];

  return (
    stringFields.every((field) => typeof value[field] === "string") &&
    numberFields.every((field) => isNumber(value[field])) &&
    isNullableString(value.image_url) &&
    (value.ranking_score === null || isNumber(value.ranking_score))
  );
}

function parseChatResponse(value: unknown): ChatResponse | null {
  if (!isRecord(value)) return null;
  if (
    typeof value.conversation_id !== "string" ||
    typeof value.message !== "string" ||
    typeof value.model !== "string" ||
    !Array.isArray(value.products) ||
    !value.products.every(isChatProduct)
  ) {
    return null;
  }

  return {
    conversation_id: value.conversation_id,
    message: value.message,
    model: value.model,
    products: value.products,
  };
}

function defaultErrorMessage(status: number): string {
  if (status === 404) return "Conversation not found.";
  if (status === 429) return "Các model đang bận. Vui lòng thử lại sau.";
  if (status === 502 || status === 503) {
    return "AI service is temporarily unavailable.";
  }
  if (status === 400 || status === 422) return "Tin nhắn không hợp lệ.";
  return "Không thể kết nối tới trợ lý lúc này.";
}

async function responseDetail(response: Response): Promise<string | undefined> {
  try {
    const body: unknown = await response.json();
    if (isRecord(body) && typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    // The caller still gets a controlled status-specific message.
  }
  return undefined;
}

function retryAfterSeconds(response: Response): number | undefined {
  const header = response.headers.get("Retry-After");
  if (!header) return undefined;
  const seconds = Number(header);
  return Number.isFinite(seconds) && seconds > 0 ? Math.ceil(seconds) : undefined;
}

export async function sendChatMessage(
  input: SendChatMessageInput,
): Promise<ChatResponse> {
  let response: Response;
  try {
    response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...(input.conversationId
          ? { conversation_id: input.conversationId }
          : {}),
        message: input.message,
      }),
    });
  } catch {
    throw new ChatApiError("Không thể kết nối tới trợ lý lúc này.", 0);
  }

  if (!response.ok) {
    const detail = await responseDetail(response);
    throw new ChatApiError(
      detail || defaultErrorMessage(response.status),
      response.status,
      retryAfterSeconds(response),
    );
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new ChatApiError("Trợ lý trả về dữ liệu không hợp lệ.", response.status);
  }

  const parsed = parseChatResponse(body);
  if (!parsed) {
    throw new ChatApiError("Trợ lý trả về dữ liệu không hợp lệ.", response.status);
  }
  return parsed;
}
