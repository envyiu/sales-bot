import type { Metadata } from "next";
import ChatWidget from "@/components/chat/ChatWidget";
import "./globals.css";
import "./landing.css";

export const metadata: Metadata = {
  title: "Sales Bot",
  description: "AI-powered smartphone sales advisor",
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
