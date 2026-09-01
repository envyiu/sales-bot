import Link from "next/link";

export default function Header() {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link className="brand" href="/" aria-label="Sales Bot home">
          <span className="brand__mark" aria-hidden="true">
            ✦
          </span>
          <span>Sales Bot</span>
        </Link>
        <nav className="site-nav" aria-label="Main navigation">
          <Link href="/products">Products</Link>
        </nav>
      </div>
    </header>
  );
}
