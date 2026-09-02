"use client";

import Link from "next/link";
import { Sparkles, ArrowLeft } from "lucide-react";

interface ProductDetailActionsProps {
  productName: string;
}

export default function ProductDetailActions({ productName }: ProductDetailActionsProps) {
  const handleAskAI = () => {
    const prompt = `Hãy tư vấn chi tiết cho mình về máy ${productName} (ưu nhược điểm, hiệu năng và độ phù hợp)?`;
    window.dispatchEvent(
      new CustomEvent("open-sales-bot-chat", {
        detail: { prompt },
      })
    );
    const launcher = document.querySelector<HTMLButtonElement>(".chat-widget__launcher");
    if (launcher && launcher.getAttribute("aria-expanded") !== "true") {
      launcher.click();
    }
  };

  return (
    <div className="detail-actions">
      <button
        type="button"
        onClick={handleAskAI}
        className="detail-btn-primary"
        aria-label={`Tư vấn AI về ${productName}`}
      >
        <Sparkles size={16} aria-hidden="true" />
        <span>Tư Vấn AI Về Máy Này</span>
      </button>
      <Link href="/products" className="detail-btn-secondary">
        <ArrowLeft size={16} aria-hidden="true" />
        <span>Xem Điện Thoại Khác</span>
      </Link>
    </div>
  );
}
