import Header from "@/components/Header";

export default function Loading() {
  return (
    <>
      <Header />
      <main className="products-page page-shell" aria-busy="true">
        <div className="loading-grid">
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
        </div>
      </main>
    </>
  );
}
