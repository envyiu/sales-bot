import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  offset: number;
  limit: number;
  itemCount: number;
  total: number;
  query: Record<string, string | undefined>;
}

function pageHref(
  offset: number,
  limit: number,
  query: Record<string, string | undefined>,
): string {
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  return `/products?${params.toString()}`;
}

export default function Pagination({
  offset,
  limit,
  itemCount,
  total,
  query,
}: PaginationProps) {
  const canGoPrevious = offset > 0;
  const canGoNext = offset + itemCount < total;
  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <nav className="pagination" aria-label="Phân trang sản phẩm">
      {canGoPrevious ? (
        <Link
          className="pagination__button"
          href={pageHref(Math.max(0, offset - limit), limit, query)}
          aria-label="Về trang trước"
        >
          <ChevronLeft size={16} aria-hidden="true" />
          <span>Trang trước</span>
        </Link>
      ) : (
        <span className="pagination__button pagination__button--disabled" aria-disabled="true">
          <ChevronLeft size={16} aria-hidden="true" />
          <span>Trang trước</span>
        </span>
      )}

      <div className="pagination__status" aria-current="page">
        <span>Trang {currentPage}</span>
        <span className="pagination__separator">/</span>
        <span>{totalPages}</span>
      </div>

      {canGoNext ? (
        <Link
          className="pagination__button"
          href={pageHref(offset + limit, limit, query)}
          aria-label="Sang trang tiếp theo"
        >
          <span>Trang sau</span>
          <ChevronRight size={16} aria-hidden="true" />
        </Link>
      ) : (
        <span className="pagination__button pagination__button--disabled" aria-disabled="true">
          <span>Trang sau</span>
          <ChevronRight size={16} aria-hidden="true" />
        </span>
      )}
    </nav>
  );
}
