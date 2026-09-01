import Link from "next/link";

import ProductImage from "@/components/ProductImage";
import { formatPrice } from "@/lib/format";
import type { ProductListItem } from "@/lib/types";

interface ProductCardProps {
  product: ProductListItem;
}

export default function ProductCard({ product }: ProductCardProps) {
  const inStock = product.stock_quantity > 0;

  return (
    <article className="product-card">
      <Link className="product-card__link" href={`/products/${product.slug}`}>
        <div className="product-card__image">
          <ProductImage src={product.image_url} alt={product.name} />
        </div>
        <div className="product-card__body">
          <p className="product-card__brand">{product.brand}</p>
          <h2>{product.name}</h2>
          <p className="product-card__price">{formatPrice(product.price_vnd)}</p>
          <p className="product-card__meta">
            {product.ram_gb} GB RAM • {product.storage_gb} GB
          </p>
          <p
            className={`stock ${
              inStock ? "stock--available" : "stock--unavailable"
            }`}
          >
            {inStock ? "Còn hàng" : "Hết hàng"}
          </p>
        </div>
      </Link>
    </article>
  );
}
