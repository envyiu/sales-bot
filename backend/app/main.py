from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.router import api_router
from app.auth.telemetry import emit_auth_event
from app.db.session import get_db


app = FastAPI(
    title="Sales Bot API",
    description="Foundation API for the sales chatbot.",
)
app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    path_events = {
        "/api/auth/register": "auth_register_failure",
        "/api/auth/login": "auth_login_failure",
    }
    event = path_events.get(request.url.path)
    if event:
        emit_auth_event(event, outcome="failure", reason="validation_failed")
    errors = jsonable_encoder(exc.errors())
    if isinstance(errors, list):
        for error in errors:
            if not isinstance(error, dict):
                continue
            location = error.get("loc")
            if isinstance(location, list) and any(
                field in {"password", "confirm_password"}
                for field in location
            ):
                error.pop("input", None)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
async def database_health(
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        await db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    return {"status": "ok", "database": "connected"}
