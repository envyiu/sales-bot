import Link from "next/link";
import { Sparkles, ChevronRight } from "lucide-react";

export default function Header() {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link className="brand" href="/" aria-label="ChoTien - Trang chủ">
          <span className="brand__mark" aria-hidden="true">
            <Sparkles size={16} />
          </span>
          <span className="brand__text">
            Cho<span className="brand__highlight">Tien</span>
          </span>
        </Link>
        <nav className="site-nav" aria-label="Main navigation">
          <Link href="/" className="site-nav__link">
            Trang Chủ
          </Link>
          <Link href="/products" className="site-nav__link">
            Cửa Hàng
          </Link>
          <a href="/#ai-advisor" className="site-nav__link">
            Tư Vấn AI
          </a>
        </nav>
        <div className="site-header__actions">
          <Link href="/products" className="nav-pill-btn">
            <span>Khám phá</span>
            <ChevronRight size={14} aria-hidden="true" />
          </Link>
        </div>
      </div>
    </header>
  );
}
