import Link from "next/link";

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
            <p className="eyebrow">Bộ Sưu Tập Chính Hãng</p>
            <h1>Khám Phá Smartphone Đỉnh Cao</h1>
            <p>So sánh thông số, đánh giá hiệu năng và lựa chọn thiết bị hoàn hảo cho bạn.</p>
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
            <h2>Không tìm thấy sản phẩm phù hợp.</h2>
            <p>Hãy thử tìm kiếm với từ khóa khác hoặc điều chỉnh lại khoảng giá.</p>
            <div style={{ marginTop: "1.5rem" }}>
              <Link className="empty-state__btn" href="/products">
                Xem Tất Cả Sản Phẩm
              </Link>
            </div>
          </div>
        ) : (
          <>
            <p className="results-count">
              Hiển thị {products.items.length} trên {products.total} sản phẩm
            </p>
            <section className="product-grid" aria-label="Danh sách smartphone">
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
