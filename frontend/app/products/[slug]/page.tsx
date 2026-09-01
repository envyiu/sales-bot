import Link from "next/link";
import { notFound } from "next/navigation";

import Header from "@/components/Header";
import ProductImage from "@/components/ProductImage";
import { getProduct } from "@/lib/api";
import { formatPrice } from "@/lib/format";

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const product = await getProduct(slug);

  if (!product) {
    notFound();
  }

  const inStock = product.inventory.quantity > 0;

  return (
    <>
      <Header />
      <main className="detail-page page-shell">
        <p className="breadcrumb">
          <Link href="/products">Products</Link> / {product.name}
        </p>
        <article className="detail-card">
          <div className="detail-card__image">
            <ProductImage src={product.image_url} alt={product.name} />
          </div>
          <div>
            <p className="detail-card__brand">{product.brand}</p>
            <h1>{product.name}</h1>
            <p className="detail-card__price">{formatPrice(product.price_vnd)}</p>
            <p
              className={`stock ${
                inStock ? "stock--available" : "stock--unavailable"
              }`}
            >
              {inStock ? `Còn hàng · ${product.inventory.quantity} sản phẩm` : "Hết hàng"}
            </p>
            {product.description ? (
              <p className="detail-card__description">{product.description}</p>
            ) : null}

            <section className="spec-section" aria-labelledby="spec-title">
              <h2 id="spec-title">Specifications</h2>
              <dl className="spec-grid">
                <div className="spec-grid__item">
                  <dt>Chipset</dt>
                  <dd>{product.spec.chipset}</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Memory</dt>
                  <dd>{product.spec.ram_gb} GB RAM</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Storage</dt>
                  <dd>{product.spec.storage_gb} GB</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Screen</dt>
                  <dd>
                    {product.spec.screen_size_inches}″ {product.spec.screen_type}
                  </dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Refresh rate</dt>
                  <dd>{product.spec.refresh_rate_hz} Hz</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Battery</dt>
                  <dd>{product.spec.battery_mah} mAh</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Charging</dt>
                  <dd>{product.spec.charging_watt} W</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>OS</dt>
                  <dd>{product.spec.os}</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Rear camera</dt>
                  <dd>{product.spec.rear_camera}</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Front camera</dt>
                  <dd>{product.spec.front_camera}</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Gaming</dt>
                  <dd>{product.spec.gaming_score}/10</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Camera</dt>
                  <dd>{product.spec.camera_score}/10</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Battery score</dt>
                  <dd>{product.spec.battery_score}/10</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Performance</dt>
                  <dd>{product.spec.performance_score}/10</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Display</dt>
                  <dd>{product.spec.display_score}/10</dd>
                </div>
              </dl>
            </section>
          </div>
        </article>
      </main>
    </>
  );
}
