import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    message_to_dict,
    messages_from_dict,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm import LLMConfigurationError, get_llm
from app.agent.prompts import SYSTEM_PROMPT
from app.models import Conversation, Message


logger = logging.getLogger(__name__)
HISTORY_MESSAGE_LIMIT = 20


class ChatServiceError(RuntimeError):
    """Base error for failures in the chat service."""


class ConversationNotFoundError(ChatServiceError):
    """Raised when a requested conversation does not exist."""


class ChatHistoryError(ChatServiceError):
    """Raised when persisted message history cannot be rehydrated."""


class ChatPersistenceError(ChatServiceError):
    """Raised when the successful chat turn cannot be persisted."""


class InvalidChatResponseError(ChatServiceError):
    """Raised when the provider returns no visible assistant text."""


class ChatProviderError(ChatServiceError):
    """Base error for provider failures that should not become fake success."""


class ChatProviderAuthenticationError(ChatProviderError):
    """Raised when Gemini rejects authentication or authorization."""


class ChatProviderRateLimitError(ChatProviderError):
    """Raised when Gemini rate-limits the request."""


class ChatProviderTemporaryError(ChatProviderError):
    """Raised when Gemini is temporarily unavailable."""


def _message_role(message: BaseMessage) -> str:
    roles = {"human": "user", "ai": "assistant", "tool": "tool"}
    try:
        return roles[message.type]
    except KeyError as exc:
        raise ChatHistoryError(
            f"Unsupported persisted LangChain message type: {message.type}"
        ) from exc


def _rehydrate_messages(rows: list[Message]) -> list[BaseMessage]:
    payloads: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row.message_payload, dict):
            raise ChatHistoryError("Persisted message payload must be a JSON object")
        payloads.append(row.message_payload)

    try:
        return messages_from_dict(payloads)
    except (KeyError, TypeError, ValueError) as exc:
        raise ChatHistoryError("Persisted LangChain message payload is invalid") from exc


def _visible_text(message: AIMessage) -> str:
    try:
        text = message.text
    except (AttributeError, TypeError, ValueError) as exc:
        raise InvalidChatResponseError("Gemini returned no visible assistant text") from exc

    if not isinstance(text, str) or not text.strip():
        raise InvalidChatResponseError("Gemini returned no visible assistant text")
    return text.strip()


def _provider_error(exc: Exception) -> ChatProviderError:
    error_name = type(exc).__name__.lower()
    error_text = str(exc).lower()
    combined = f"{error_name} {error_text}"

    if any(
        marker in combined
        for marker in (
            "unauthenticated",
            "permissiondenied",
            "authentication",
            "invalid api key",
            "api key not valid",
        )
    ):
        return ChatProviderAuthenticationError("Gemini authentication failed")

    if any(
        marker in combined
        for marker in (
            "resourceexhausted",
            "resource_exhausted",
            "rate limit",
            "ratelimit",
            "quota",
        )
    ):
        return ChatProviderRateLimitError("Gemini rate limit reached")

    if any(
        marker in combined
        for marker in (
            "serviceunavailable",
            "internalserver",
            "deadlineexceeded",
            "timeout",
            "connection",
            "temporarily unavailable",
            "statuscode=503",
        )
    ):
        return ChatProviderTemporaryError("Gemini is temporarily unavailable")

    return ChatProviderError("Gemini request failed")


async def _invoke_llm(messages: list[BaseMessage], conversation_id: UUID) -> AIMessage:
    try:
        llm = get_llm()
    except LLMConfigurationError:
        logger.warning(
            "llm_call",
            extra={
                "event": "llm_call",
                "conversation_id": str(conversation_id),
                "status": "configuration_error",
            },
        )
        raise
    except Exception as exc:
        logger.warning(
            "llm_call",
            extra={
                "event": "llm_call",
                "conversation_id": str(conversation_id),
                "status": "configuration_error",
                "error_type": type(exc).__name__,
            },
        )
        raise LLMConfigurationError("Gemini client configuration is invalid") from exc

    try:
        response = await llm.ainvoke(messages)
    except Exception as exc:
        provider_error = _provider_error(exc)
        logger.warning(
            "llm_call",
            extra={
                "event": "llm_call",
                "conversation_id": str(conversation_id),
                "status": "provider_error",
                "error_type": type(exc).__name__,
            },
        )
        raise provider_error from exc

    if not isinstance(response, AIMessage):
        raise InvalidChatResponseError("Gemini returned an unexpected message type")

    logger.info(
        "llm_call",
        extra={
            "event": "llm_call",
            "conversation_id": str(conversation_id),
            "status": "success",
        },
    )
    return response


async def generate_chat_reply(
    session: AsyncSession,
    message: str,
    conversation_id: UUID | None = None,
) -> tuple[UUID, str]:
    history: list[BaseMessage] = []

    if conversation_id is not None:
        conversation = await session.get(Conversation, conversation_id)
        if conversation is None:
            raise ConversationNotFoundError("Conversation not found")

        result = await session.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
            .limit(HISTORY_MESSAGE_LIMIT)
        )
        history_rows = list(result.all())
        history_rows.reverse()
        history = _rehydrate_messages(history_rows)
        await session.rollback()

    target_conversation_id = conversation_id or uuid4()
    human_message = HumanMessage(content=message)
    llm_messages = [SystemMessage(content=SYSTEM_PROMPT), *history, human_message]
    ai_message = await _invoke_llm(llm_messages, target_conversation_id)
    visible_text = _visible_text(ai_message)

    try:
        human_payload = message_to_dict(human_message)
        assistant_payload = message_to_dict(ai_message)
        if conversation_id is None:
            session.add(Conversation(id=target_conversation_id))
        else:
            await session.execute(
                update(Conversation)
                .where(Conversation.id == target_conversation_id)
                .values(updated_at=datetime.now(timezone.utc))
            )

        session.add_all(
            [
                Message(
                    conversation_id=target_conversation_id,
                    role=_message_role(human_message),
                    content_text=message,
                    message_payload=human_payload,
                ),
                Message(
                    conversation_id=target_conversation_id,
                    role=_message_role(ai_message),
                    content_text=visible_text,
                    message_payload=assistant_payload,
                ),
            ]
        )
        await session.commit()
    except Exception as exc:
        await session.rollback()
        raise ChatPersistenceError("Chat turn could not be persisted") from exc

    return target_conversation_id, visible_text
