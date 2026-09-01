import Header from "@/components/Header";
import Pagination from "@/components/Pagination";
import ProductCard from "@/components/ProductCard";
import ProductFilters from "@/components/ProductFilters";
import { getProducts } from "@/lib/api";
import type { ProductSort } from "@/lib/types";

const PAGE_SIZE = 12;
const validSorts: ProductSort[] = [
  "newest",
  "price_asc",
  "price_desc",
  "name_asc",
];

type SearchParams = Record<string, string | string[] | undefined>;

function firstValue(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function numberValue(value: string | undefined): number | undefined {
  if (!value) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export default async function ProductsPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;
  const q = firstValue(params.q);
  const brand = firstValue(params.brand);
  const minPrice = firstValue(params.min_price);
  const maxPrice = firstValue(params.max_price);
  const requestedSort = firstValue(params.sort);
  const sort: ProductSort = validSorts.includes(requestedSort as ProductSort)
    ? (requestedSort as ProductSort)
    : "newest";
  const requestedOffset = numberValue(firstValue(params.offset));
  const offset = requestedOffset !== undefined && requestedOffset >= 0
    ? Math.floor(requestedOffset)
    : 0;

  const products = await getProducts({
    q,
    brand: brand ? [brand] : undefined,
    min_price: numberValue(minPrice),
    max_price: numberValue(maxPrice),
    limit: PAGE_SIZE,
    offset,
    sort,
  });

  const query = {
    q,
    brand,
    min_price: minPrice,
    max_price: maxPrice,
    sort,
  };

  return (
    <>
      <Header />
      <main className="products-page page-shell">
        <div className="page-heading">
          <div>
            <p className="eyebrow">Smartphone catalog</p>
            <h1>Find your next phone</h1>
            <p>Compare the essentials and choose with confidence.</p>
          </div>
        </div>

        <ProductFilters
          q={q}
          brand={brand}
          minPrice={minPrice}
          maxPrice={maxPrice}
          sort={sort}
        />

        {products.total === 0 ? (
          <div className="empty-state">
            <h2>No phones found matching your filters.</h2>
            <p>Try a different search or broaden your price range.</p>
          </div>
        ) : (
          <>
            <p className="results-count">
              Showing {products.items.length} of {products.total} phones
            </p>
            <section className="product-grid" aria-label="Products">
              {products.items.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </section>
            <Pagination
              offset={products.offset}
              limit={products.limit}
              itemCount={products.items.length}
              total={products.total}
              query={query}
            />
          </>
        )}
      </main>
    </>
  );
}
