"use client";

import { useState } from "react";
import { Smartphone } from "lucide-react";

interface ProductImageProps {
  src: string | null;
  alt: string;
}

// Fallback mapping for demo data pointing to example.com
function resolveImageUrl(src: string | null, alt: string): string | null {
  if (!src) return null;
  if (src.includes("example.com")) {
    const lower = (src + " " + alt).toLowerCase();
    if (lower.includes("iphone")) return "/images/iphone-16-pro.jpg";
    if (lower.includes("galaxy") || lower.includes("samsung")) return "/images/galaxy-s25.jpg";
    if (lower.includes("pixel") || lower.includes("google")) return "/images/pixel-9.jpg";
    if (lower.includes("gaming") || lower.includes("14t")) return "/images/gaming-phone.jpg";
    return "/images/camera-tech.jpg";
  }
  return src;
}

export default function ProductImage({ src, alt }: ProductImageProps) {
  const [hasError, setHasError] = useState(false);
  const resolvedSrc = resolveImageUrl(src, alt);

  if (!resolvedSrc || hasError) {
    return (
      <div className="product-image__fallback" role="img" aria-label={alt}>
        <Smartphone className="product-image__fallback-icon" size={48} strokeWidth={1.5} aria-hidden="true" />
      </div>
    );
  }

  return (
    <img
      className="product-image"
      src={resolvedSrc}
      alt={alt}
      loading="lazy"
      onError={() => setHasError(true)}
    />
  );
}
