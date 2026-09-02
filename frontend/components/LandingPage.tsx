"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  Sparkles,
  ChevronRight,
  Zap,
  ShieldCheck,
  Smartphone,
  Cpu,
  Camera,
  BatteryCharging,
  SlidersHorizontal,
  Bot,
  Layers
} from "lucide-react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import { formatPrice } from "@/lib/format";
import type { ProductDetail } from "@/lib/types";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

const FLAGSHIPS = [
  {
    slug: "apple-iphone-16-pro-max",
    name: "iPhone 16 Pro Max",
    brand: "Apple",
    headline: "Đỉnh cao Titanium. A18 Pro.",
    price: "34.990.000₫",
    chipset: "Apple A18 Pro",
    camera: "48MP main + 48MP ultrawide + 12MP telephoto",
    battery: "4.685 mAh • 30W",
    display: "6.9\" LTPO Super Retina XDR 120Hz",
    image: "/images/iphone-16-pro.jpg",
    highlight: "Titanium Tự Nhiên",
  },
  {
    slug: "samsung-galaxy-s25-ultra",
    name: "Galaxy S25 Ultra",
    brand: "Samsung",
    headline: "Quyền năng Galaxy AI. 200MP.",
    price: "33.990.000₫",
    chipset: "Snapdragon 8 Elite",
    camera: "200MP Quad Cam 5x OIS",
    battery: "5.000 mAh • 45W",
    display: "6.8\" Dynamic AMOLED 2X 120Hz",
    image: "/images/galaxy-s25.jpg",
    highlight: "Galaxy AI Tích Hợp",
  },
  {
    slug: "xiaomi-15-ultra",
    name: "Xiaomi 15 Ultra",
    brand: "Xiaomi",
    headline: "Huyền thoại nhiếp ảnh Leica.",
    price: "29.990.000₫",
    chipset: "Snapdragon 8 Elite",
    camera: "50MP 1-inch Quad Leica",
    battery: "5.400 mAh • 90W",
    display: "6.73\" AMOLED 2K 120Hz",
    image: "/images/camera-tech.jpg",
    highlight: "Ống Kính Leica Vario",
  },
  {
    slug: "google-pixel-9-pro-xl",
    name: "Pixel 9 Pro XL",
    brand: "Google",
    headline: "Trí tuệ Google Gemini thuần khiết.",
    price: "26.990.000₫",
    chipset: "Google Tensor G4",
    camera: "50MP Triple Pro Camera",
    battery: "5.060 mAh • 37W",
    display: "6.8\" Super Actua LTPO 120Hz",
    image: "/images/pixel-9.jpg",
    highlight: "Cập Nhật 7 Năm",
  },
];

const APPLE_PILLARS = [
  {
    icon: Bot,
    title: "AI Thấu Hiểu Nhu Cầu",
    desc: "Mô hình ngôn ngữ lớn phân tích thói quen sử dụng, ngân sách và sở thích cá nhân để đưa ra lựa chọn chính xác trong vài giây.",
  },
  {
    icon: SlidersHorizontal,
    title: "So Sánh Kỹ Thuật Đa Chiều",
    desc: "Bóc tách sự khác biệt thực tế giữa các chipset A18 Pro và Snapdragon 8 Elite, cảm biến camera và thời lượng pin thực tế.",
  },
  {
    icon: Layers,
    title: "Kho Hàng Trực Tuyến Tức Thì",
    desc: "Đồng bộ hóa dữ liệu thời gian thực với hệ thống kho, đảm bảo thiết bị bạn chọn luôn sẵn sàng giao ngay.",
  },
  {
    icon: ShieldCheck,
    title: "Bảo Hành Toàn Diện 100%",
    desc: "Phân phối chính hãng đầy đủ tem bảo hành nhà sản xuất, đổi mới 30 ngày và chăm sóc trọn đời.",
  },
];

interface LandingPageProps {
  initialProducts?: ProductDetail[];
}

export default function LandingPage({ initialProducts = [] }: LandingPageProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const heroImageRef = useRef<HTMLDivElement>(null);

  const productMap = new Map(initialProducts.map((p) => [p.slug, p]));
  const heroProduct = productMap.get("apple-iphone-16-pro-max");
  const heroPrice = heroProduct ? formatPrice(heroProduct.price_vnd) : "34.990.000₫";

  const flagships = FLAGSHIPS.map((phone) => {
    const live = productMap.get(phone.slug);
    if (!live) {
      return {
        ...phone,
        stockStatus: "Còn hàng",
        inStock: true,
      };
    }
    const spec = live.spec;
    const inStock = live.inventory.quantity > 0;
    return {
      slug: live.slug,
      name: live.name,
      brand: live.brand,
      headline: phone.headline,
      price: formatPrice(live.price_vnd),
      chipset: spec.chipset,
      camera: spec.rear_camera,
      battery: `${spec.battery_mah.toLocaleString()} mAh • ${spec.charging_watt}W`,
      display: `${spec.screen_size_inches}" ${spec.screen_type} ${spec.refresh_rate_hz}Hz`,
      image: phone.image,
      highlight: phone.highlight,
      stockStatus: inStock ? `Còn ${live.inventory.quantity} máy` : "Tạm hết hàng",
      inStock,
    };
  });

  useEffect(() => {
    const isReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (isReducedMotion) return;

    const ctx = gsap.context(() => {
      // 1. Hero headline fade and slight scale
      gsap.from(".apple-hero-anim", {
        y: 30,
        opacity: 0,
        duration: 1.2,
        stagger: 0.15,
        ease: "power3.out",
      });

      // 2. Hero device cinematic reveal
      gsap.from(".apple-hero-device", {
        scale: 0.88,
        opacity: 0,
        y: 40,
        duration: 1.4,
        ease: "power3.out",
        delay: 0.2,
      });

      // Hero image scrub parallax
      if (heroImageRef.current) {
        gsap.to(heroImageRef.current, {
          yPercent: 15,
          scale: 1.05,
          ease: "none",
          scrollTrigger: {
            trigger: ".apple-hero",
            start: "top top",
            end: "bottom top",
            scrub: 1,
          },
        });
      }

      // 3. Cinematic Chapters Scroll Zoom
      const chapterCards = gsap.utils.toArray<HTMLElement>(".apple-chapter");
      chapterCards.forEach((chapter) => {
        const image = chapter.querySelector(".chapter-image");
        const copy = chapter.querySelector(".chapter-copy");

        if (image) {
          gsap.fromTo(
            image,
            { scale: 1.15, filter: "brightness(0.7)" },
            {
              scale: 1,
              filter: "brightness(1)",
              ease: "none",
              scrollTrigger: {
                trigger: chapter,
                start: "top 80%",
                end: "top 20%",
                scrub: 1,
              },
            }
          );
        }

        if (copy) {
          gsap.from(copy, {
            y: 40,
            opacity: 0,
            duration: 0.9,
            ease: "power2.out",
            scrollTrigger: {
              trigger: chapter,
              start: "top 70%",
              toggleActions: "play none none reverse",
            },
          });
        }
      });

      // 4. Stagger reveal for product cards
      gsap.from(".apple-card", {
        scrollTrigger: {
          trigger: ".apple-grid",
          start: "top 78%",
          toggleActions: "play none none reverse",
        },
        y: 40,
        opacity: 0,
        duration: 0.8,
        stagger: 0.12,
        ease: "power3.out",
      });

      // 5. Apple Intelligence Card Pulse
      gsap.from(".ai-intelligence-card", {
        scrollTrigger: {
          trigger: ".ai-intelligence-card",
          start: "top 80%",
          toggleActions: "play none none reverse",
        },
        scale: 0.95,
        opacity: 0,
        duration: 1,
        ease: "power3.out",
      });

    }, containerRef);

    return () => ctx.revert();
  }, []);

  const handleOpenChat = () => {
    window.dispatchEvent(new CustomEvent("open-sales-bot-chat"));
  };

  return (
    <div ref={containerRef} className="apple-root">
      {/* 1. CINEMATIC HERO SECTION */}
      <section className="apple-hero" aria-labelledby="hero-title">
        <div className="apple-container apple-hero__content">
          <div className="apple-hero__header">
            <span className="apple-eyebrow apple-hero-anim">Thế Hệ Smartphone 2025</span>
            <h1 id="hero-title" className="apple-headline-hero apple-hero-anim">
              Titanium. Trí Tuệ AI. <br />
              <span className="shimmer-text">Đỉnh Cao Hoàn Mỹ.</span>
            </h1>
            <p className="apple-subhead apple-hero-anim">
              Hội tụ những tuyệt tác di động hàng đầu thế giới, được thấu hiểu và đề xuất chuẩn xác bởi trợ lý AI ChoTien.
            </p>

            <div className="apple-hero__cta apple-hero-anim">
              <Link href="/products" className="apple-btn-primary">
                Khám Phá Cửa Hàng
              </Link>
              <button
                type="button"
                onClick={handleOpenChat}
                className="apple-btn-glass"
              >
                <span>Tư Vấn Cùng AI</span>
                <ChevronRight size={16} aria-hidden="true" />
              </button>
            </div>
          </div>

          {/* HERO CENTERPIECE DEVICE */}
          <div className="apple-hero-device" ref={heroImageRef}>
            <div className="apple-device-frame">
              <div className="device-ambient-glow" aria-hidden="true" />
              <Image
                src="/images/iphone-16-pro.jpg"
                alt="iPhone 16 Pro Max Titanium Studio Presentation"
                width={512}
                height={640}
                priority
                className="apple-device-img"
              />
              <div className="device-spec-overlay">
                <span className="device-pill">Flagship Nổi Bật</span>
                <h3 className="device-title">{heroProduct ? heroProduct.name : "iPhone 16 Pro Max"}</h3>
                <p className="device-price">Từ {heroPrice}</p>
              </div>
            </div>

            {/* FLOATING STAT PILLS (APPLE GLASS STYLE) */}
            <div className="apple-glass-pill apple-glass-pill--left">
              <div className="pill-metric">A18 Pro</div>
              <div className="pill-caption">Tiến trình 3nm • Đồ họa Ray Tracing</div>
            </div>

            <div className="apple-glass-pill apple-glass-pill--right">
              <div className="pill-metric">48MP 5X</div>
              <div className="pill-caption">Quang học tiềm vọng • 4K 120fps</div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. CINEMATIC CHAPTER 1: CAMERA & PHOTOGRAPHY */}
      <section className="apple-chapter apple-chapter--camera" aria-labelledby="chapter-camera-title">
        <div className="apple-container">
          <div className="chapter-copy">
            <span className="chapter-eyebrow">Hệ Thống Nhiếp Ảnh Chuyên Nghiệp</span>
            <h2 id="chapter-camera-title" className="chapter-title">
              Cảm Biến 1-inch. <br />
              Bắt Trọn Từng Khoảnh Khắc.
            </h2>
            <p className="chapter-desc">
              Khẩu độ siêu lớn kết hợp thuật toán tính toán nhiếp ảnh AI đem lại độ chi tiết phi thường, màu sắc chân thực và dải tương phản động vượt chuẩn rạp chiếu phim.
            </p>

            <div className="apple-specs-bar">
              <div className="spec-block">
                <div className="spec-huge">50MP</div>
                <div className="spec-sub">Độ Phân Giải Siêu Cảm Biến</div>
              </div>
              <div className="spec-block">
                <div className="spec-huge">5X</div>
                <div className="spec-sub">Thu Phóng Tiềm Vọng Quang Học</div>
              </div>
              <div className="spec-block">
                <div className="spec-huge">4K 120</div>
                <div className="spec-sub">Chuẩn Điện Ảnh Dolby Vision</div>
              </div>
            </div>
          </div>

          <div className="chapter-media-wrap">
            <Image
              src="/images/camera-tech.jpg"
              alt="Hệ thống camera smartphone cao cấp"
              width={560}
              height={385}
              className="chapter-image"
            />
          </div>
        </div>
      </section>

      {/* 3. CINEMATIC CHAPTER 2: CRAFTSMANSHIP & TITANIUM */}
      <section className="apple-chapter apple-chapter--reverse" aria-labelledby="chapter-craft-title">
        <div className="apple-container">
          <div className="chapter-copy">
            <span className="chapter-eyebrow">Thiết Kế &amp; Hoàn Thiện</span>
            <h2 id="chapter-craft-title" className="chapter-title">
              Titanium Hàng Không. <br />
              Cực Bền. Nhẹ Đáng Kinh Ngạc.
            </h2>
            <p className="chapter-desc">
              Vật liệu chế tác từ hợp kim Titanium cấp độ 5 với tỷ lệ bền trên khối lượng tốt nhất trong thế giới kim loại, viền màn hình siêu mỏng mở rộng tầm nhìn bất tận.
            </p>

            <div className="apple-specs-bar">
              <div className="spec-block">
                <div className="spec-huge">Grade 5</div>
                <div className="spec-sub">Hợp Kim Titanium Cao Cấp</div>
              </div>
              <div className="spec-block">
                <div className="spec-huge">2.600 nits</div>
                <div className="spec-sub">Độ Sáng Màn Hình Cực Đại</div>
              </div>
              <div className="spec-block">
                <div className="spec-huge">120Hz</div>
                <div className="spec-sub">Tần Số Quét Thích Ứng LTPO</div>
              </div>
            </div>
          </div>

          <div className="chapter-media-wrap">
            <Image
              src="/images/galaxy-s25.jpg"
              alt="Khung viền Titanium và màn hình Dynamic AMOLED"
              width={560}
              height={385}
              className="chapter-image"
            />
          </div>
        </div>
      </section>

      {/* 4. CINEMATIC CHAPTER 3: POWER & CHIPSET */}
      <section className="apple-chapter apple-chapter--performance" aria-labelledby="chapter-perf-title">
        <div className="apple-container">
          <div className="chapter-copy">
            <span className="chapter-eyebrow">Hiệu Năng Vô Địch</span>
            <h2 id="chapter-perf-title" className="chapter-title">
              Kiến Trúc 3 Nanometer. <br />
              Sức Mạnh Thay Đổi Cuộc Chơi.
            </h2>
            <p className="chapter-desc">
              Bứt phá mọi giới hạn đồ họa gaming và xử lý tác vụ trí tuệ nhân tạo trên máy với hiệu suất năng lượng tối ưu, kéo dài thời lượng pin suốt cả ngày dài.
            </p>

            <div className="apple-specs-bar">
              <div className="spec-block">
                <div className="spec-huge">3nm</div>
                <div className="spec-sub">Tiến Trình Chế Tác Đột Phá</div>
              </div>
              <div className="spec-block">
                <div className="spec-huge">9.8/10</div>
                <div className="spec-sub">Điểm Đánh Giá Gaming Đỉnh Cao</div>
              </div>
              <div className="spec-block">
                <div className="spec-huge">5.400 mAh</div>
                <div className="spec-sub">Dung Lượng Pin Thế Hệ Mới</div>
              </div>
            </div>
          </div>

          <div className="chapter-media-wrap">
            <Image
              src="/images/gaming-phone.jpg"
              alt="Hiệu năng gaming cực đại"
              width={560}
              height={385}
              className="chapter-image"
            />
          </div>
        </div>
      </section>

      {/* 5. APPLE-STYLE PRODUCT LINEUP COMPARISON */}
      <section className="apple-lineup-section" aria-labelledby="lineup-title">
        <div className="apple-container">
          <div className="apple-section-header">
            <span className="apple-eyebrow">Bộ Sưu Tập Nổi Bật</span>
            <h2 id="lineup-title" className="apple-headline">
              Chọn Thiết Bị Phù Hợp Nhất Với Bạn.
            </h2>
            <p className="apple-subtext">
              So sánh các dòng flagship mới nhất và tìm ra phiên bản hoàn hảo cho phong cách sống của bạn.
            </p>
          </div>

          <div className="apple-grid">
            {flagships.map((phone) => (
              <article key={phone.slug} className="apple-card">
                <div className="apple-card__media">
                  <div className="apple-card__badges">
                    <span className="apple-card__highlight">{phone.highlight}</span>
                    <span
                      className={`apple-card__stock-badge ${
                        phone.inStock
                          ? "apple-card__stock-badge--in"
                          : "apple-card__stock-badge--out"
                      }`}
                    >
                      {phone.stockStatus}
                    </span>
                  </div>
                  <Image
                    src={phone.image}
                    alt={phone.name}
                    width={380}
                    height={285}
                    className="apple-card__img"
                  />
                </div>

                <div className="apple-card__body">
                  <span className="apple-card__brand">{phone.brand}</span>
                  <h3 className="apple-card__title">{phone.name}</h3>
                  <p className="apple-card__headline">{phone.headline}</p>

                  <div className="apple-card__price">{phone.price}</div>

                  <div className="apple-card__specs">
                    <div className="apple-spec-line">
                      <Cpu size={14} className="spec-icon" aria-hidden="true" />
                      <span>{phone.chipset}</span>
                    </div>
                    <div className="apple-spec-line">
                      <Camera size={14} className="spec-icon" aria-hidden="true" />
                      <span>{phone.camera}</span>
                    </div>
                    <div className="apple-spec-line">
                      <Smartphone size={14} className="spec-icon" aria-hidden="true" />
                      <span>{phone.display}</span>
                    </div>
                    <div className="apple-spec-line">
                      <BatteryCharging size={14} className="spec-icon" aria-hidden="true" />
                      <span>{phone.battery}</span>
                    </div>
                  </div>

                  <div className="apple-card__actions">
                    <Link href={`/products/${phone.slug}`} className="apple-btn-buy">
                      Xem Chi Tiết
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* 6. APPLE INTELLIGENCE / AI ADVISOR SHOWCASE */}
      <section id="ai-advisor" className="apple-intelligence-section" aria-labelledby="ai-title">
        <div className="apple-container">
          <div className="ai-intelligence-card">
            <div className="ai-intelligence-glow" aria-hidden="true" />

            <div className="ai-intelligence-inner">
              <div className="ai-intelligence-copy">
                <div className="ai-tag">
                  <Sparkles size={14} className="ai-sparkle" aria-hidden="true" />
                  <span>ChoTien Intelligence</span>
                </div>
                <h2 id="ai-title" className="ai-headline">
                  Trí Tuệ Nhân Tạo. <br />
                  <span className="iridescent-text">Hiểu Đúng Điều Bạn Cần.</span>
                </h2>
                <p className="ai-description">
                  Không phải ai cũng am hiểu công nghệ vi xử lý hay khẩu độ ống kính. Chỉ cần chia sẻ những điều bạn quan tâm, AI ChoTien sẽ giúp bạn chọn ra sản phẩm đúng giá trị và hợp nhu cầu nhất.
                </p>

                <div className="ai-actions">
                  <button
                    type="button"
                    onClick={handleOpenChat}
                    className="apple-btn-primary"
                  >
                    Bắt Đầu Tư Vấn Ngay
                  </button>
                </div>
              </div>

              {/* LIVE SIMULATED DIALOGUE */}
              <div className="ai-simulation-panel" aria-hidden="true">
                <div className="sim-bubble sim-bubble--user">
                  <p>Mình muốn tìm một chiếc điện thoại chụp ảnh sắc nét khi đi du lịch và pin trâu trong ngày, tài chính khoảng 25-30 triệu?</p>
                </div>

                <div className="sim-bubble sim-bubble--ai">
                  <div className="sim-ai-brand">
                    <Sparkles size={13} className="sim-ai-icon" />
                    <span>ChoTien AI (Gemini 2.5 Flash)</span>
                  </div>
                  <p>
                    Với nhu cầu chụp ảnh du lịch và pin bền bỉ trong khoảng 25 - 30 triệu, <strong>Xiaomi 15 Ultra</strong> (29.990.000₫) và <strong>Pixel 9 Pro XL</strong> (26.990.000₫) là sự lựa chọn xuất sắc nhất! Cả hai máy đều sở hữu cụm camera tiềm vọng hàng đầu và pin trên 5.000 mAh.
                  </p>
                  <div className="sim-card-compact">
                    <Image
                      src="/images/camera-tech.jpg"
                      alt="Xiaomi 15 Ultra"
                      width={52}
                      height={52}
                      className="sim-card-img"
                    />
                    <div className="sim-card-info">
                      <span className="sim-card-name">Xiaomi 15 Ultra</span>
                      <span className="sim-card-stock">● Sẵn hàng trong kho</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 7. APPLE PILLARS */}
      <section className="apple-pillars-section">
        <div className="apple-container">
          <div className="pillars-grid">
            {APPLE_PILLARS.map((item, index) => {
              const IconComponent = item.icon;
              return (
                <div key={index} className="pillar-item">
                  <div className="pillar-icon-box">
                    <IconComponent size={24} />
                  </div>
                  <h3 className="pillar-title">{item.title}</h3>
                  <p className="pillar-desc">{item.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 8. CLIMAX BOTTOM CTA */}
      <section className="apple-climax-section">
        <div className="apple-container apple-climax-inner">
          <span className="apple-eyebrow">Trải Nghiệm Mua Sắm Cao Cấp</span>
          <h2 className="climax-title">Tìm Chiếc Smartphone Đích Thực Của Bạn.</h2>
          <p className="climax-sub">Giao hàng miễn phí toàn quốc. Bảo hành chính hãng 100%. Tư vấn AI 24/7.</p>
          <div className="climax-actions">
            <Link href="/products" className="apple-btn-primary apple-btn-lg">
              Khám Phá Toàn Bộ Sản Phẩm
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
