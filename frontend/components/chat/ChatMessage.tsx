import ChatProductCard from "@/components/chat/ChatProductCard";
import type { ChatMessage as ChatMessageData } from "@/lib/chat-types";

interface ChatMessageProps {
  message: ChatMessageData;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const products = message.products ?? [];

  return (
    <article className={`chat-message chat-message--${message.role}`}>
      <div className="chat-message__bubble">
        <p>{message.content}</p>
      </div>
      {message.role === "assistant" && message.model ? (
        <p className="chat-message__model">Phản hồi bởi {message.model}</p>
      ) : null}
      {products.length > 0 ? (
        <div className="chat-message__products" aria-label="Điện thoại được đề xuất">
          {products.map((product) => (
            <ChatProductCard key={product.id} product={product} />
          ))}
        </div>
      ) : null}
    </article>
  );
}
