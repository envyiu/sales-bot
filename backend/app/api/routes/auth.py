from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_auth
from app.auth.sessions import AuthContext
from app.auth.telemetry import emit_auth_event
from app.db.session import get_db
from app.schemas.auth import AuthResponse, LoginRequest, MeResponse, RegisterRequest
from app.services.auth import (
    DuplicateEmailError,
    InvalidCredentialsError,
    login_user,
    register_user,
    revoke_session,
)


router = APIRouter()


def _client_ip(request: Request) -> str | None:
    return request.headers.get("x-auth-client-ip") or (
        request.client.host if request.client is not None else None
    )


def _user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user and create a session",
)
async def register(
    payload: RegisterRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> AuthResponse:
    try:
        result = await register_user(
            session,
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
        )
    except DuplicateEmailError as exc:
        emit_auth_event(
            "auth_register_failure",
            outcome="failure",
            reason="duplicate_email",
            email=payload.email,
            client_ip=_client_ip(request),
            user_agent=_user_agent(request),
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration could not be completed for this email.",
        ) from exc
    except Exception as exc:
        emit_auth_event(
            "auth_register_failure",
            outcome="failure",
            reason="service_error",
            email=payload.email,
            client_ip=_client_ip(request),
            user_agent=_user_agent(request),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Registration could not be completed.",
        ) from exc

    emit_auth_event(
        "auth_register_success",
        outcome="success",
        user_id=result.user.id,
        session_id=result.session.id,
        email=result.user.email,
        client_ip=_client_ip(request),
        user_agent=_user_agent(request),
    )
    return AuthResponse(
        id=result.user.id,
        email=result.user.email,
        display_name=result.user.display_name,
        created_at=result.user.created_at,
        session_expires_at=result.session.expires_at,
        session_token=result.raw_token,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Verify credentials and create a session",
)
async def login(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> AuthResponse:
    try:
        result = await login_user(
            session,
            email=payload.email,
            password=payload.password,
        )
    except InvalidCredentialsError as exc:
        emit_auth_event(
            "auth_login_failure",
            outcome="failure",
            reason="invalid_credentials",
            email=payload.email,
            client_ip=_client_ip(request),
            user_agent=_user_agent(request),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from exc
    except Exception as exc:
        emit_auth_event(
            "auth_login_failure",
            outcome="failure",
            reason="service_error",
            email=payload.email,
            client_ip=_client_ip(request),
            user_agent=_user_agent(request),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login could not be completed.",
        ) from exc

    emit_auth_event(
        "auth_login_success",
        outcome="success",
        user_id=result.user.id,
        session_id=result.session.id,
        email=result.user.email,
        client_ip=_client_ip(request),
        user_agent=_user_agent(request),
    )
    return AuthResponse(
        id=result.user.id,
        email=result.user.email,
        display_name=result.user.display_name,
        created_at=result.user.created_at,
        session_expires_at=result.session.expires_at,
        session_token=result.raw_token,
    )


@router.post("/logout", summary="Revoke the current session")
async def logout(
    request: Request,
    auth_context: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await revoke_session(session, auth_context)
    emit_auth_event(
        "auth_logout",
        outcome="success",
        reason="user_requested",
        user_id=auth_context.user.id,
        session_id=auth_context.session.id,
        client_ip=_client_ip(request),
        user_agent=_user_agent(request),
    )
    return {"detail": "Logged out"}


@router.get("/me", response_model=MeResponse, summary="Get the current user")
async def me(
    auth_context: AuthContext = Depends(get_current_auth),
) -> MeResponse:
    return MeResponse(
        id=auth_context.user.id,
        email=auth_context.user.email,
        display_name=auth_context.user.display_name,
        created_at=auth_context.user.created_at,
        session_expires_at=auth_context.session.expires_at,
    )
