from enum import Enum

from pydantic import BaseModel, Field, model_validator


class ProductSort(str, Enum):
    price_asc = "price_asc"
    price_desc = "price_desc"
    newest = "newest"
    name_asc = "name_asc"


class ProductFilters(BaseModel):
    q: str | None = Field(default=None, max_length=200)
    brand: list[str] | None = None
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    min_ram: int | None = Field(default=None, ge=0)
    min_storage: int | None = Field(default=None, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort: ProductSort = ProductSort.newest

    @model_validator(mode="after")
    def validate_price_range(self) -> "ProductFilters":
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("min_price must be less than or equal to max_price")
        return self


class ProductListItem(BaseModel):
    id: int
    slug: str
    name: str
    brand: str
    model: str
    price_vnd: int
    image_url: str | None
    release_year: int | None
    ram_gb: int
    storage_gb: int
    stock_quantity: int


class ProductListResponse(BaseModel):
    items: list[ProductListItem]
    total: int
    limit: int
    offset: int


class ProductSpecResponse(BaseModel):
    chipset: str
    ram_gb: int
    storage_gb: int
    screen_size_inches: float
    screen_type: str
    refresh_rate_hz: int
    battery_mah: int
    charging_watt: int
    rear_camera: str
    front_camera: str
    os: str
    gaming_score: float
    camera_score: float
    battery_score: float
    performance_score: float
    display_score: float


class InventoryResponse(BaseModel):
    quantity: int


class ProductDetailResponse(BaseModel):
    id: int
    slug: str
    name: str
    brand: str
    model: str
    price_vnd: int
    description: str | None
    image_url: str | None
    release_year: int | None
    is_active: bool
    spec: ProductSpecResponse
    inventory: InventoryResponse
