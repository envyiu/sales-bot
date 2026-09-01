"use client";

import { useState } from "react";

interface ProductImageProps {
  src: string | null;
  alt: string;
}

export default function ProductImage({ src, alt }: ProductImageProps) {
  const [hasError, setHasError] = useState(false);

  if (!src || hasError) {
    return (
      <div className="product-image__fallback" role="img" aria-label={alt}>
        <span aria-hidden="true">📱</span>
      </div>
    );
  }

  return (
    <img
      className="product-image"
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setHasError(true)}
    />
  );
}
