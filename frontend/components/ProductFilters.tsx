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
  return (
    <form className="filter-panel" action="/products" method="get">
      <label className="field">
        Search
        <input name="q" type="search" placeholder="Search phones" defaultValue={q} />
      </label>

      <label className="field">
        Brand
        <select name="brand" defaultValue={brand ?? ""}>
          <option value="">All brands</option>
          <option value="Apple">Apple</option>
          <option value="Samsung">Samsung</option>
          <option value="Xiaomi">Xiaomi</option>
          <option value="OPPO">OPPO</option>
          <option value="Google">Google</option>
        </select>
      </label>

      <label className="field">
        Min price
        <input name="min_price" type="number" min="0" defaultValue={minPrice} />
      </label>

      <label className="field">
        Max price
        <input name="max_price" type="number" min="0" defaultValue={maxPrice} />
      </label>

      <label className="field">
        Sort
        <select name="sort" defaultValue={sort}>
          <option value="newest">Newest</option>
          <option value="price_asc">Price: Low to High</option>
          <option value="price_desc">Price: High to Low</option>
          <option value="name_asc">Name</option>
        </select>
      </label>

      <button className="button button--primary" type="submit">
        Apply
      </button>
    </form>
  );
}
