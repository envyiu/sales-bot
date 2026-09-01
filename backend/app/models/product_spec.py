from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.product import Product


class ProductSpec(Base):
    __tablename__ = "product_specs"
    __table_args__ = (
        CheckConstraint("ram_gb >= 0", name="ck_product_specs_ram_non_negative"),
        CheckConstraint("storage_gb >= 0", name="ck_product_specs_storage_non_negative"),
        CheckConstraint("screen_size_inches > 0", name="ck_product_specs_screen_size_positive"),
        CheckConstraint("refresh_rate_hz > 0", name="ck_product_specs_refresh_rate_positive"),
        CheckConstraint("battery_mah >= 0", name="ck_product_specs_battery_non_negative"),
        CheckConstraint("charging_watt >= 0", name="ck_product_specs_charging_non_negative"),
        CheckConstraint(
            "gaming_score >= 0 AND gaming_score <= 10",
            name="ck_product_specs_gaming_score_range",
        ),
        CheckConstraint(
            "camera_score >= 0 AND camera_score <= 10",
            name="ck_product_specs_camera_score_range",
        ),
        CheckConstraint(
            "battery_score >= 0 AND battery_score <= 10",
            name="ck_product_specs_battery_score_range",
        ),
        CheckConstraint(
            "performance_score >= 0 AND performance_score <= 10",
            name="ck_product_specs_performance_score_range",
        ),
        CheckConstraint(
            "display_score >= 0 AND display_score <= 10",
            name="ck_product_specs_display_score_range",
        ),
    )

    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    chipset: Mapped[str] = mapped_column(String(255), nullable=False)
    ram_gb: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    storage_gb: Mapped[int] = mapped_column(Integer, nullable=False)
    screen_size_inches: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    screen_type: Mapped[str] = mapped_column(String(100), nullable=False)
    refresh_rate_hz: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    battery_mah: Mapped[int] = mapped_column(Integer, nullable=False)
    charging_watt: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    rear_camera: Mapped[str] = mapped_column(String(255), nullable=False)
    front_camera: Mapped[str] = mapped_column(String(255), nullable=False)
    os: Mapped[str] = mapped_column(String(100), nullable=False)
    gaming_score: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    camera_score: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    battery_score: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    performance_score: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    display_score: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)

    product: Mapped["Product"] = relationship(back_populates="spec")
