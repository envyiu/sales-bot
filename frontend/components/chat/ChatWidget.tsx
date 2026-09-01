"use client";

import { useCallback, useEffect, useState } from "react";

import ChatPanel from "@/components/chat/ChatPanel";
import { ChatApiError, sendChatMessage } from "@/lib/chat-api";
import type { ChatMessage } from "@/lib/chat-types";

const STORAGE_KEY = "sales_bot_conversation_id";
const WELCOME_MESSAGE: ChatMessage = {
  id: "welcome-message",
  role: "assistant",
  content: "Xin chào! Mình có thể giúp bạn tìm điện thoại theo ngân sách và nhu cầu.",
};

function errorMessage(error: unknown): string {
  if (!(error instanceof ChatApiError)) {
    return "Không thể kết nối tới trợ lý lúc này.";
  }
  if (error.status === 404) {
    return "Phiên chat cũ không còn tồn tại. Hãy gửi lại tin nhắn để bắt đầu phiên mới.";
  }
  if (error.status === 429) {
    return error.retryAfter
      ? `Các model đang bận. Thử lại sau khoảng ${error.retryAfter} giây.`
      : "Các model đang bận. Vui lòng thử lại sau.";
  }
  if (error.status === 502 || error.status === 503) {
    return "AI service is temporarily unavailable.";
  }
  if (error.status === 400 || error.status === 422) {
    return "Tin nhắn không hợp lệ. Hãy thử viết lại ngắn gọn hơn.";
  }
  return error.message;
}

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedConversationId = window.localStorage.getItem(STORAGE_KEY);
    if (storedConversationId) setConversationId(storedConversationId);
    setIsReady(true);
  }, []);

  const closePanel = useCallback(() => setIsOpen(false), []);

  function startNewChat() {
    if (isSending) return;
    window.localStorage.removeItem(STORAGE_KEY);
    setConversationId(null);
    setMessages([WELCOME_MESSAGE]);
    setError(null);
  }

  async function handleSend(message: string): Promise<void> {
    if (!isReady || isSending || !message.trim()) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: message,
    };
    setMessages((current) => [...current, userMessage]);
    setError(null);
    setIsSending(true);

    try {
      const response = await sendChatMessage({
        conversationId,
        message,
      });
      setConversationId(response.conversation_id);
      window.localStorage.setItem(STORAGE_KEY, response.conversation_id);
      setMessages((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response.message,
          model: response.model,
          products: response.products,
        },
      ]);
    } catch (requestError) {
      if (requestError instanceof ChatApiError && requestError.status === 404) {
        window.localStorage.removeItem(STORAGE_KEY);
        setConversationId(null);
      }
      setError(errorMessage(requestError));
    } finally {
      setIsSending(false);
    }
  }

  return (
    <aside className="chat-widget">
      {isOpen ? (
        <ChatPanel
          messages={messages}
          isSending={isSending}
          isReady={isReady}
          error={error}
          onClose={closePanel}
          onNewChat={startNewChat}
          onSend={handleSend}
        />
      ) : null}
      <button
        className="chat-widget__launcher"
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        aria-expanded={isOpen}
        aria-controls="sales-bot-chat-panel"
        aria-label={isOpen ? "Close AI smartphone advisor" : "Open AI smartphone advisor"}
      >
        <span aria-hidden="true">✦</span>
        <span>{isOpen ? "Close" : "Chat"}</span>
      </button>
    </aside>
  );
}
