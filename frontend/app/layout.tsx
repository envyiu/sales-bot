import type { Metadata } from "next";
import ChatWidget from "@/components/chat/ChatWidget";
import "./globals.css";

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
    <html lang="en">
      <body>
        {children}
        <ChatWidget />
      </body>
    </html>
  );
}
