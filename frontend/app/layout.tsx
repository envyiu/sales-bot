import type { Metadata } from "next";
import ChatWidget from "@/components/chat/ChatWidget";
import "./globals.css";
import "./landing.css";

export const metadata: Metadata = {
  title: "ChoTien - Trợ lý AI Smartphone",
  description: "ChoTien - Trợ lý tư vấn bán hàng smartphone AI thông minh",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body>
        {children}
        <ChatWidget />
      </body>
    </html>
  );
}
