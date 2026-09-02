import Link from "next/link";
import { Compass, ArrowLeft } from "lucide-react";

import Header from "@/components/Header";

export default function NotFound() {
  return (
    <>
      <Header />
      <main className="products-page page-shell">
        <div className="empty-state">
          <div className="empty-state__icon-box" aria-hidden="true">
            <Compass size={40} strokeWidth={1.5} />
          </div>
          <p className="eyebrow">404 · Lỗi Đường Dẫn</p>
          <h1>Không Tìm Thấy Trang Hoặc Sản Phẩm</h1>
          <p>Thiết bị bạn đang tìm kiếm có thể đã thay đổi đường dẫn hoặc tạm ngừng kinh doanh.</p>
          <div style={{ marginTop: "2rem" }}>
            <Link className="empty-state__btn" href="/products">
              <ArrowLeft size={16} aria-hidden="true" />
              <span>Quay Lại Cửa Hàng</span>
            </Link>
          </div>
        </div>
      </main>
    </>
  );
}
