import Link from "next/link";

import ProductImage from "@/components/ProductImage";
import { formatPrice } from "@/lib/format";
import type { ChatProduct } from "@/lib/chat-types";

interface ChatProductCardProps {
  product: ChatProduct;
}

export default function ChatProductCard({ product }: ChatProductCardProps) {
  const inStock = product.stock_quantity > 0;

  return (
    <Link className="chat-product-card" href={`/products/${product.slug}`}>
      <div className="chat-product-card__image">
        <ProductImage src={product.image_url} alt={product.name} />
      </div>
      <div className="chat-product-card__body">
        <p className="chat-product-card__brand">{product.brand}</p>
        <h4>{product.name}</h4>
        <p className="chat-product-card__price">{formatPrice(product.price_vnd)}</p>
        <p className="chat-product-card__meta">
          {product.ram_gb} GB RAM · {product.storage_gb} GB · {product.chipset}
        </p>
        <p className={inStock ? "chat-stock chat-stock--available" : "chat-stock"}>
          {inStock ? `Còn ${product.stock_quantity} máy` : "Hết hàng"}
        </p>
      </div>
    </Link>
  );
}
