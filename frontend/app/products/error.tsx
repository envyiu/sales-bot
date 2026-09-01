"use client";

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
        <p className="eyebrow">Catalog unavailable</p>
        <h1>We couldn&apos;t load the phones.</h1>
        <p>{error.message || "Please try again in a moment."}</p>
        <button className="button button--primary" type="button" onClick={reset}>
          Try again
        </button>
      </div>
    </main>
  );
}
