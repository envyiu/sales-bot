import json
import logging
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any


logger = logging.getLogger("app.auth")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def email_fingerprint(email: str) -> str:
    return sha256(normalize_email(email).encode("utf-8")).hexdigest()


def emit_auth_event(
    event: str,
    *,
    outcome: str,
    reason: str | None = None,
    user_id: object | None = None,
    session_id: object | None = None,
    email: str | None = None,
    client_ip: str | None = None,
    user_agent: str | None = None,
    conversation_id: object | None = None,
) -> None:
    payload: dict[str, Any] = {
        "event": event,
        "outcome": outcome,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if reason:
        payload["reason"] = reason
    if user_id is not None:
        payload["user_id"] = str(user_id)
    if session_id is not None:
        payload["session_id"] = str(session_id)
    if email is not None:
        payload["email_fingerprint"] = email_fingerprint(email)
    if client_ip:
        payload["client_ip"] = client_ip
    if user_agent:
        payload["user_agent"] = user_agent
    if conversation_id is not None:
        payload["conversation_id"] = str(conversation_id)

    logger.info(json.dumps(payload, ensure_ascii=False, sort_keys=True))
