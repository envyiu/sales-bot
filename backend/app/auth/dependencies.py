from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.sessions import (
    AuthContext,
    ExpiredSessionError,
    InactiveUserSessionError,
    RevokedSessionError,
    UnknownSessionError,
    get_auth_context,
)
from app.auth.telemetry import emit_auth_event
from app.db.session import get_db
from app.models import User


def _client_ip(request: Request) -> str | None:
    # The BFF supplies this value for telemetry only. It is never used for authz.
    return request.headers.get("x-auth-client-ip") or (
        request.client.host if request.client is not None else None
    )


def _user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


def _unauthorized(detail: str = "Authentication required") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _parse_bearer_token(authorization: str | None) -> str:
    if authorization is None:
        raise ValueError("missing authorization header")
    scheme, separator, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not separator or not token.strip():
        raise ValueError("invalid authorization header")
    return token.strip()


async def _resolve_auth_context(
    request: Request,
    authorization: str | None,
    session: AsyncSession,
    *,
    optional: bool,
) -> AuthContext | None:
    if authorization is None and optional:
        return None

    try:
        raw_token = _parse_bearer_token(authorization)
    except ValueError:
        emit_auth_event(
            "auth_session_invalid",
            outcome="failure",
            reason="invalid_authorization_header",
            client_ip=_client_ip(request),
            user_agent=_user_agent(request),
        )
        raise _unauthorized() from None

    try:
        return await get_auth_context(session, raw_token)
    except UnknownSessionError:
        emit_auth_event(
            "auth_session_invalid",
            outcome="failure",
            reason="unknown_session",
            client_ip=_client_ip(request),
            user_agent=_user_agent(request),
        )
    except ExpiredSessionError as exc:
        emit_auth_event(
            "auth_session_expired",
            outcome="failure",
            reason="expired",
            session_id=exc.session_id,
            client_ip=_client_ip(request),
            user_agent=_user_agent(request),
        )
    except RevokedSessionError as exc:
        emit_auth_event(
            "auth_session_revoked",
            outcome="failure",
            reason="revoked",
            session_id=exc.session_id,
            client_ip=_client_ip(request),
            user_agent=_user_agent(request),
        )
    except InactiveUserSessionError as exc:
        emit_auth_event(
            "auth_session_invalid",
            outcome="failure",
            reason="inactive_account",
            session_id=exc.session_id,
            client_ip=_client_ip(request),
            user_agent=_user_agent(request),
        )

    raise _unauthorized() from None


async def get_current_auth(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_db),
) -> AuthContext:
    context = await _resolve_auth_context(
        request,
        authorization,
        session,
        optional=False,
    )
    assert context is not None
    return context


async def get_current_user(
    context: AuthContext = Depends(get_current_auth),
) -> User:
    return context.user


async def get_optional_current_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_db),
) -> User | None:
    context = await _resolve_auth_context(
        request,
        authorization,
        session,
        optional=True,
    )
    return context.user if context is not None else None
