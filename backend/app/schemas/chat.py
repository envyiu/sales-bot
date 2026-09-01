from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    conversation_id: UUID | None = None
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        message = value.strip()
        if not message:
            raise ValueError("message must not be blank")
        return message


class ChatProduct(BaseModel):
    id: int
    slug: str
    name: str
    brand: str
    model: str
    price_vnd: int
    image_url: str | None
    ram_gb: int
    storage_gb: int
    chipset: str
    battery_mah: int
    gaming_score: float
    battery_score: float
    performance_score: float
    stock_quantity: int
    ranking_score: float | None


class ChatResponse(BaseModel):
    conversation_id: UUID
    message: str
    products: list[ChatProduct] = Field(default_factory=list)
