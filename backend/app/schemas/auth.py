from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _normalize_email(value: str) -> str:
    email = value.strip().lower()
    local, separator, domain = email.partition("@")
    if (
        not separator
        or not local
        or not domain
        or "." not in domain
        or any(character.isspace() for character in email)
    ):
        raise ValueError("Enter a valid email address")
    return email


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=128)
    display_name: str | None = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def normalize_and_validate_email(cls, value: str) -> str:
        return _normalize_email(value)

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_and_validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    email: str
    display_name: str | None
    created_at: datetime


class AuthResponse(UserResponse):
    session_expires_at: datetime
    session_token: str


class MeResponse(UserResponse):
    session_expires_at: datetime
