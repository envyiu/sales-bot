import Link from "next/link";
import { Search, RotateCcw } from "lucide-react";

import type { ProductSort } from "@/lib/types";

interface ProductFiltersProps {
  q?: string;
  brand?: string;
  minPrice?: string;
  maxPrice?: string;
  sort: ProductSort;
}

export default function ProductFilters({
  q,
  brand,
  minPrice,
  maxPrice,
  sort,
}: ProductFiltersProps) {
  const hasActiveFilters = Boolean(q || brand || minPrice || maxPrice || sort !== "newest");

  return (
    <form className="filter-panel" action="/products" method="get">
      <label className="field">
        <span className="field__label">Tìm kiếm</span>
        <div className="field__input-wrap">
          <input
            name="q"
            type="search"
            placeholder="Tên máy, tính năng..."
            defaultValue={q}
          />
        </div>
      </label>

      <label className="field">
        <span className="field__label">Thương hiệu</span>
        <select name="brand" defaultValue={brand ?? ""}>
          <option value="">Tất cả thương hiệu</option>
          <option value="Apple">Apple (iPhone)</option>
          <option value="Samsung">Samsung (Galaxy)</option>
          <option value="Xiaomi">Xiaomi</option>
          <option value="OPPO">OPPO</option>
          <option value="Google">Google (Pixel)</option>
        </select>
      </label>

      <label className="field">
        <span className="field__label">Giá từ (VNĐ)</span>
        <input
          name="min_price"
          type="number"
          min="0"
          step="500000"
          placeholder="Tối thiểu"
          defaultValue={minPrice}
        />
      </label>

      <label className="field">
        <span className="field__label">Giá đến (VNĐ)</span>
        <input
          name="max_price"
          type="number"
          min="0"
          step="500000"
          placeholder="Tối đa"
          defaultValue={maxPrice}
        />
      </label>

      <label className="field">
        <span className="field__label">Sắp xếp</span>
        <select name="sort" defaultValue={sort}>
          <option value="newest">Mới nhất</option>
          <option value="price_asc">Giá: Thấp đến Cao</option>
          <option value="price_desc">Giá: Cao đến Thấp</option>
          <option value="name_asc">Tên: A - Z</option>
        </select>
      </label>

      <div className="filter-actions">
        <button className="filter-btn-apply" type="submit">
          <span>Áp dụng</span>
        </button>
        {hasActiveFilters ? (
          <Link
            className="filter-btn-reset"
            href="/products"
            title="Xóa toàn bộ bộ lọc"
            aria-label="Xóa toàn bộ bộ lọc"
          >
            <RotateCcw size={15} />
          </Link>
        ) : null}
      </div>
    </form>
  );
}
