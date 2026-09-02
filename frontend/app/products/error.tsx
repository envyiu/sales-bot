"use client";

import { AlertCircle, RefreshCw } from "lucide-react";

interface ProductsErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ProductsError({
  error,
  reset,
}: ProductsErrorProps) {
  return (
    <main className="products-page page-shell">
      <div className="error-state" role="alert">
        <div className="error-state__icon-box" aria-hidden="true">
          <AlertCircle size={40} strokeWidth={1.5} />
        </div>
        <p className="eyebrow">Lỗi Kết Nối Danh Mục</p>
        <h1>Không Thể Tải Danh Sách Smartphone</h1>
        <p>{error.message || "Hệ thống đang bận hoặc gián đoạn kết nối. Vui lòng thử lại."}</p>
        <div style={{ marginTop: "2rem" }}>
          <button className="error-state__btn" type="button" onClick={reset}>
            <RefreshCw size={16} aria-hidden="true" />
            <span>Thử Lại Ngay</span>
          </button>
        </div>
      </div>
    </main>
  );
}
