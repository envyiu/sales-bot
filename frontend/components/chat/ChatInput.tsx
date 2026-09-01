import { FormEvent, KeyboardEvent, useState } from "react";

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
        Message for AI smartphone advisor
      </label>
      <textarea
        id="chat-message-input"
        name="message"
        value={value}
        maxLength={4000}
        rows={1}
        placeholder="Type a message..."
        aria-label="Message for AI smartphone advisor"
        disabled={disabled}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
      />
      <button
        className="chat-input__send"
        type="submit"
        disabled={disabled || !value.trim()}
      >
        Send
      </button>
    </form>
  );
}
