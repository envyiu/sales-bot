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


class ChatResponse(BaseModel):
    conversation_id: UUID
    message: str
