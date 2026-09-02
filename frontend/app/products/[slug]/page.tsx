import Link from "next/link";
import { notFound } from "next/navigation";
import { Cpu, Smartphone, ShieldCheck, Zap } from "lucide-react";

import Header from "@/components/Header";
import ProductDetailActions from "@/components/ProductDetailActions";
import ProductImage from "@/components/ProductImage";
import { getProduct } from "@/lib/api";
import { formatPrice } from "@/lib/format";

function ScoreBar({ label, score }: { label: string; score: number }) {
  const percentage = Math.min(100, Math.max(0, (score / 10) * 100));
  return (
    <div className="spec-score-item">
      <div className="spec-score-header">
        <span className="spec-score-label">{label}</span>
        <span className="spec-score-val">{score}/10</span>
      </div>
      <div className="spec-score-track" aria-hidden="true">
        <div className="spec-score-fill" style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}

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
        <nav className="breadcrumb" aria-label="Đường dẫn trang">
          <Link href="/products">Cửa Hàng</Link>
          <span className="breadcrumb__separator">/</span>
          <span className="breadcrumb__current">{product.name}</span>
        </nav>

        <article className="detail-card">
          <div className="detail-card__image-col">
            <div className="detail-card__image">
              <ProductImage src={product.image_url} alt={product.name} />
              <div className="detail-image-badges">
                <span className="detail-badge detail-badge--brand">{product.brand}</span>
                <span
                  className={`detail-badge ${
                    inStock ? "detail-badge--available" : "detail-badge--unavailable"
                  }`}
                >
                  {inStock ? `Còn hàng (${product.inventory.quantity})` : "Hết hàng"}
                </span>
              </div>
            </div>

            <div className="detail-trust-pills">
              <div className="trust-pill">
                <ShieldCheck size={16} className="trust-pill__icon" />
                <span>Chính hãng 100%</span>
              </div>
              <div className="trust-pill">
                <Zap size={16} className="trust-pill__icon" />
                <span>Giao nhanh 2h</span>
              </div>
            </div>
          </div>

          <div className="detail-card__info-col">
            <p className="detail-card__brand">{product.brand}</p>
            <h1 className="detail-card__title">{product.name}</h1>
            <p className="detail-card__price">{formatPrice(product.price_vnd)}</p>

            {product.description ? (
              <p className="detail-card__description">{product.description}</p>
            ) : null}

            <ProductDetailActions productName={product.name} />

            <section className="spec-section" aria-labelledby="benchmark-title">
              <h2 id="benchmark-title" className="spec-heading">
                Điểm Đánh Giá Trải Nghiệm
              </h2>
              <div className="spec-scores-grid">
                <ScoreBar label="Gaming" score={product.spec.gaming_score} />
                <ScoreBar label="Nhiếp ảnh (Camera)" score={product.spec.camera_score} />
                <ScoreBar label="Thời lượng pin" score={product.spec.battery_score} />
                <ScoreBar label="Hiệu năng tổng thể" score={product.spec.performance_score} />
                <ScoreBar label="Chất lượng hiển thị" score={product.spec.display_score} />
              </div>
            </section>

            <section className="spec-section" aria-labelledby="spec-title">
              <h2 id="spec-title" className="spec-heading">
                Thông Số Kỹ Thuật
              </h2>
              <dl className="spec-grid">
                <div className="spec-grid__item">
                  <dt>Vi xử lý (Chipset)</dt>
                  <dd>{product.spec.chipset}</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Bộ nhớ RAM</dt>
                  <dd>{product.spec.ram_gb} GB</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Bộ nhớ trong</dt>
                  <dd>{product.spec.storage_gb} GB</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Màn hình</dt>
                  <dd>
                    {product.spec.screen_size_inches}″ {product.spec.screen_type}
                  </dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Tần số quét</dt>
                  <dd>{product.spec.refresh_rate_hz} Hz</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Dung lượng pin</dt>
                  <dd>{product.spec.battery_mah} mAh</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Công suất sạc nhanh</dt>
                  <dd>{product.spec.charging_watt} W</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Hệ điều hành</dt>
                  <dd>{product.spec.os}</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Camera sau</dt>
                  <dd>{product.spec.rear_camera}</dd>
                </div>
                <div className="spec-grid__item">
                  <dt>Camera trước</dt>
                  <dd>{product.spec.front_camera}</dd>
                </div>
              </dl>
            </section>
          </div>
        </article>
      </main>
    </>
  );
}
