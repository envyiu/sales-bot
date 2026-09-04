import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AuthSession, User


SESSION_TOKEN_BYTES = 32


class SessionLookupError(RuntimeError):
    """Base error for session authentication failures."""

    def __init__(self, message: str, *, session_id: UUID | None = None) -> None:
        super().__init__(message)
        self.session_id = session_id


class UnknownSessionError(SessionLookupError):
    """Raised when no session matches the presented token."""


class ExpiredSessionError(SessionLookupError):
    """Raised when a matching session is past its expiry."""


class RevokedSessionError(SessionLookupError):
    """Raised when a matching session has been revoked."""


class InactiveUserSessionError(SessionLookupError):
    """Raised when a matching session belongs to an inactive user."""


@dataclass(frozen=True, slots=True)
class AuthContext:
    user: User
    session: AuthSession


def generate_session_token() -> str:
    return secrets.token_urlsafe(SESSION_TOKEN_BYTES)


def hash_session_token(raw_token: str) -> str:
    return sha256(raw_token.encode("utf-8")).hexdigest()


def session_expiry(now: datetime, ttl_seconds: int) -> datetime:
    return now + timedelta(seconds=ttl_seconds)


def new_auth_session(
    user: User,
    *,
    now: datetime,
    ttl_seconds: int,
) -> tuple[AuthSession, str]:
    raw_token = generate_session_token()
    auth_session = AuthSession(
        user_id=user.id,
        token_hash=hash_session_token(raw_token),
        created_at=now,
        expires_at=session_expiry(now, ttl_seconds),
    )
    return auth_session, raw_token


async def get_auth_context(
    session: AsyncSession,
    raw_token: str,
    *,
    now: datetime | None = None,
) -> AuthContext:
    auth_session = await session.scalar(
        select(AuthSession)
        .options(selectinload(AuthSession.user))
        .where(AuthSession.token_hash == hash_session_token(raw_token))
    )
    if auth_session is None:
        raise UnknownSessionError("Session not found")

    current_time = now or datetime.now(timezone.utc)
    if auth_session.revoked_at is not None:
        raise RevokedSessionError(
            "Session has been revoked",
            session_id=auth_session.id,
        )
    if auth_session.expires_at <= current_time:
        raise ExpiredSessionError(
            "Session has expired",
            session_id=auth_session.id,
        )
    if not auth_session.user.is_active:
        raise InactiveUserSessionError(
            "User is inactive",
            session_id=auth_session.id,
        )

    return AuthContext(user=auth_session.user, session=auth_session)
