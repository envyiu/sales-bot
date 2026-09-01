import Link from "next/link";

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

  return (
    <nav className="pagination" aria-label="Product pages">
      {canGoPrevious ? (
        <Link
          className="pagination__button"
          href={pageHref(Math.max(0, offset - limit), limit, query)}
        >
          Previous
        </Link>
      ) : (
        <span className="pagination__button pagination__button--disabled">Previous</span>
      )}
      {canGoNext ? (
        <Link
          className="pagination__button"
          href={pageHref(offset + limit, limit, query)}
        >
          Next
        </Link>
      ) : (
        <span className="pagination__button pagination__button--disabled">Next</span>
      )}
    </nav>
  );
}
