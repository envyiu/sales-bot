import Link from "next/link";

import Header from "@/components/Header";

export default function NotFound() {
  return (
    <>
      <Header />
      <main className="products-page page-shell">
        <div className="empty-state">
          <p className="eyebrow">404</p>
          <h1>Phone not found</h1>
          <p>That product may have moved or is no longer available.</p>
          <Link className="button button--primary" href="/products">
            Back to products
          </Link>
        </div>
      </main>
    </>
  );
}
