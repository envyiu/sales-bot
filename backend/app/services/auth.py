from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.passwords import DUMMY_PASSWORD_HASH, hash_password, verify_password
from app.auth.sessions import AuthContext, new_auth_session
from app.auth.telemetry import normalize_email
from app.core.config import get_settings
from app.models import AuthSession, User


class AuthServiceError(RuntimeError):
    """Base error for authentication service failures."""


class DuplicateEmailError(AuthServiceError):
    """Raised when an email is already registered."""


class InvalidCredentialsError(AuthServiceError):
    """Raised for unknown, wrong-password, or inactive accounts."""


@dataclass(frozen=True, slots=True)
class AuthResult:
    user: User
    session: AuthSession
    raw_token: str


async def register_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    display_name: str | None,
) -> AuthResult:
    normalized_email = normalize_email(email)
    existing = await session.scalar(select(User).where(User.email == normalized_email))
    if existing is not None:
        await session.rollback()
        raise DuplicateEmailError("Email is already registered")

    now = datetime.now(timezone.utc)
    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        display_name=display_name.strip() if display_name else None,
        created_at=now,
        updated_at=now,
    )
    session.add(user)

    try:
        await session.flush()
        auth_session, raw_token = new_auth_session(
            user,
            now=now,
            ttl_seconds=get_settings().auth_session_ttl_seconds,
        )
        session.add(auth_session)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateEmailError("Email is already registered") from exc
    except Exception:
        await session.rollback()
        raise

    return AuthResult(user=user, session=auth_session, raw_token=raw_token)


async def login_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
) -> AuthResult:
    normalized_email = normalize_email(email)
    user = await session.scalar(select(User).where(User.email == normalized_email))
    password_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    password_matches = verify_password(password, password_hash)

    if user is None or not password_matches or not user.is_active:
        await session.rollback()
        raise InvalidCredentialsError("Invalid email or password")

    now = datetime.now(timezone.utc)
    try:
        auth_session, raw_token = new_auth_session(
            user,
            now=now,
            ttl_seconds=get_settings().auth_session_ttl_seconds,
        )
        session.add(auth_session)
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return AuthResult(user=user, session=auth_session, raw_token=raw_token)


async def revoke_session(
    session: AsyncSession,
    auth_context: AuthContext,
) -> bool:
    result = await session.execute(
        update(AuthSession)
        .where(
            AuthSession.id == auth_context.session.id,
            AuthSession.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(timezone.utc))
    )
    await session.commit()
    return bool(result.rowcount)
