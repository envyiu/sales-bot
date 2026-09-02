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
  const panelRef = useRef<HTMLElement>(null);
  const viewportRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    // Store currently focused element before opening
    previousFocusRef.current = document.activeElement as HTMLElement | null;

    // Auto-focus input
    const input = panelRef.current?.querySelector<HTMLTextAreaElement>("#chat-message-input");
    if (input) {
      input.focus();
    }

    return () => {
      // Restore focus to launcher on close
      if (previousFocusRef.current && typeof previousFocusRef.current.focus === "function") {
        previousFocusRef.current.focus();
      } else {
        const launcher = document.querySelector<HTMLButtonElement>(".chat-widget__launcher");
        launcher?.focus();
      }
    };
  }, []);

  useEffect(() => {
    const viewport = viewportRef.current;
    if (viewport) viewport.scrollTop = viewport.scrollHeight;
  }, [messages, isSending, error]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }

      if (event.key === "Tab") {
        const panel = panelRef.current;
        if (!panel) return;

        const focusableElements = panel.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (event.shiftKey) {
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement.focus();
          }
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <section
      ref={panelRef}
      id="sales-bot-chat-panel"
      className="chat-panel"
      role="dialog"
      aria-modal="true"
      aria-label="Trợ lý bán hàng smartphone ChoTien"
      data-testid="chat-panel"
    >
      <header className="chat-panel__header">
        <div>
          <p className="chat-panel__eyebrow">ChoTien Intelligence</p>
          <h2>Trợ Lý Bán Hàng ChoTien</h2>
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
              <span>ChoTien đang suy nghĩ...</span>
            </div>
          </div>
        ) : null}
        {error ? <ChatError message={error} /> : null}
      </div>

      <ChatInput disabled={!isReady || isSending} onSubmit={onSend} />
    </section>
  );
}
