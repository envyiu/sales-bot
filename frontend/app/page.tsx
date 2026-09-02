import Header from "@/components/Header";
import LandingPage from "@/components/LandingPage";
import { getProduct } from "@/lib/api";
import type { ProductDetail } from "@/lib/types";

const FEATURED_SLUGS = [
  "apple-iphone-16-pro-max",
  "samsung-galaxy-s25-ultra",
  "xiaomi-15-ultra",
  "google-pixel-9-pro-xl",
];

export default async function Home() {
  const products: (ProductDetail | null)[] = await Promise.all(
    FEATURED_SLUGS.map(async (slug) => {
      try {
        return await getProduct(slug);
      } catch {
        return null;
      }
    })
  );

  return (
    <>
      <Header />
      <LandingPage
        initialProducts={products.filter((p): p is ProductDetail => p !== null)}
      />
    </>
  );
}
