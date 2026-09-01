interface ChatErrorProps {
  message: string;
}

export default function ChatError({ message }: ChatErrorProps) {
  return (
    <p className="chat-error" role="alert">
      {message}
    </p>
  );
}
