import { FormEvent, KeyboardEvent, useState } from "react";
import { Send } from "lucide-react";

interface ChatInputProps {
  disabled: boolean;
  onSubmit: (message: string) => Promise<void>;
}

export default function ChatInput({ disabled, onSubmit }: ChatInputProps) {
  const [value, setValue] = useState("");

  async function submitMessage(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const message = value.trim();
    if (!message || disabled) return;
    setValue("");
    await onSubmit(message);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submitMessage();
    }
  }

  return (
    <form className="chat-input" onSubmit={submitMessage}>
      <label className="sr-only" htmlFor="chat-message-input">
        Tin nhắn cho trợ lý AI ChoTien
      </label>
      <textarea
        id="chat-message-input"
        name="message"
        value={value}
        maxLength={4000}
        rows={1}
        placeholder="Hỏi ChoTien về camera, pin, gaming, giá máy..."
        aria-label="Tin nhắn gửi trợ lý bán hàng ChoTien"
        disabled={disabled}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
      />
      <button
        className="chat-input__send"
        type="submit"
        disabled={disabled || !value.trim()}
        aria-label="Gửi tin nhắn"
      >
        <Send size={15} aria-hidden="true" />
        <span>Gửi</span>
      </button>
    </form>
  );
}
