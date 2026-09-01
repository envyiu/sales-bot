import Link from "next/link";

import Header from "@/components/Header";

export default function Home() {
  return (
    <>
      <Header />
      <main className="home-page page-shell">
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero__content">
            <p className="eyebrow">Sales Bot</p>
            <h1 id="hero-title">Find the right smartphone for you</h1>
            <p className="hero__subtitle">
              AI-powered smartphone shopping assistant
            </p>
            <Link className="button button--primary" href="/products">
              Browse phones
            </Link>
          </div>
          <div className="hero__orb" aria-hidden="true">
            <span>✦</span>
          </div>
        </section>
      </main>
    </>
  );
}
