import { useEffect, useRef } from "react";

import ChatError from "@/components/chat/ChatError";
import ChatInput from "@/components/chat/ChatInput";
import ChatMessage from "@/components/chat/ChatMessage";
import type { ChatMessage as ChatMessageData } from "@/lib/chat-types";

interface ChatPanelProps {
  messages: ChatMessageData[];
  isSending: boolean;
  isReady: boolean;
  error: string | null;
  onClose: () => void;
  onNewChat: () => void;
  onSend: (message: string) => Promise<void>;
}

export default function ChatPanel({
  messages,
  isSending,
  isReady,
  error,
  onClose,
  onNewChat,
  onSend,
}: ChatPanelProps) {
  const viewportRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const viewport = viewportRef.current;
    if (viewport) viewport.scrollTop = viewport.scrollHeight;
  }, [messages, isSending, error]);

  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [onClose]);

  return (
    <section
      id="sales-bot-chat-panel"
      className="chat-panel"
      role="dialog"
      aria-modal="false"
      aria-label="Trợ lý bán hàng smartphone AI"
      data-testid="chat-panel"
    >
      <header className="chat-panel__header">
        <div>
          <p className="chat-panel__eyebrow">Sales Bot Intelligence</p>
          <h2>Trợ Lý Bán Hàng AI</h2>
        </div>
        <div className="chat-panel__actions">
          <button
            className="chat-panel__new"
            type="button"
            onClick={onNewChat}
            disabled={isSending}
            title="Bắt đầu đoạn chat mới"
          >
            Đoạn chat mới
          </button>
          <button
            className="chat-panel__close"
            type="button"
            onClick={onClose}
            aria-label="Đóng bảng chat"
          >
            ×
          </button>
        </div>
      </header>

      <div ref={viewportRef} className="chat-panel__messages" aria-live="polite">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        {isSending ? (
          <div className="chat-message chat-message--assistant">
            <div className="chat-message__bubble chat-message__bubble--loading">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span>Sales Bot đang suy nghĩ...</span>
            </div>
          </div>
        ) : null}
        {error ? <ChatError message={error} /> : null}
      </div>

      <ChatInput disabled={!isReady || isSending} onSubmit={onSend} />
    </section>
  );
}
