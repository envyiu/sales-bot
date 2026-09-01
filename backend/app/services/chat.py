import json
import logging
from dataclasses import dataclass
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

from app.agent.llm import LLMConfigurationError, get_llm_with_tools
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tool_executor import ToolExecution, execute_tool
from app.models import Conversation, Message, ToolCall


logger = logging.getLogger(__name__)
HISTORY_MESSAGE_LIMIT = 20
HISTORY_FETCH_LIMIT = HISTORY_MESSAGE_LIMIT * 2
MAX_TOOL_ITERATIONS = 5


@dataclass(frozen=True, slots=True)
class ChatTurnResult:
    conversation_id: UUID
    message: str
    products: list[dict[str, Any]]


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


class ToolLoopLimitError(ChatServiceError):
    """Raised when Gemini does not finish its tool loop within the hard limit."""


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


def _select_safe_history_rows(rows: list[Message]) -> list[Message]:
    """Trim history at a user boundary so a ToolMessage cannot become an orphan."""

    if not rows:
        return []

    target_start = max(0, len(rows) - HISTORY_MESSAGE_LIMIT)
    start_index: int | None = None

    # Prefer the latest user message at or before the target boundary. This can
    # retain a few extra rows when a turn contains an AI tool call and tools.
    for index in range(target_start, -1, -1):
        if rows[index].role == "user":
            start_index = index
            break

    # If the fetch window starts mid-turn, discard that partial turn and begin
    # with the next complete user turn available in the window.
    if start_index is None:
        for index in range(target_start + 1, len(rows)):
            if rows[index].role == "user":
                start_index = index
                break

    if start_index is None:
        return []
    return rows[start_index:]


def _validate_tool_protocol(history: list[BaseMessage]) -> None:
    """Reject corrupted history with unmatched tool messages before Gemini sees it."""

    pending_tool_call_ids: set[str] = set()
    for message in history:
        if message.type == "ai":
            if pending_tool_call_ids:
                raise ChatHistoryError("Persisted tool call is missing a ToolMessage")
            pending_tool_call_ids = {
                str(tool_call["id"])
                for tool_call in getattr(message, "tool_calls", [])
                if tool_call.get("id")
            }
        elif message.type == "tool":
            tool_call_id = str(getattr(message, "tool_call_id", ""))
            if tool_call_id not in pending_tool_call_ids:
                raise ChatHistoryError("Persisted ToolMessage has no matching tool call")
            pending_tool_call_ids.remove(tool_call_id)
        elif pending_tool_call_ids:
            raise ChatHistoryError("Persisted tool call is missing a ToolMessage")

    if pending_tool_call_ids:
        raise ChatHistoryError("Persisted tool call is missing a ToolMessage")


def _visible_text(message: AIMessage) -> str:
    try:
        text = message.text
    except (AttributeError, TypeError, ValueError) as exc:
        raise InvalidChatResponseError("Gemini returned no visible assistant text") from exc

    if not isinstance(text, str) or not text.strip():
        raise InvalidChatResponseError("Gemini returned no visible assistant text")
    return text.strip()


def _stored_content_text(message: BaseMessage) -> str:
    if isinstance(message, AIMessage):
        try:
            text = message.text
        except (AttributeError, TypeError, ValueError):
            text = ""
        return text.strip() if isinstance(text, str) else ""

    content = message.content
    if isinstance(content, str):
        return content
    try:
        return json.dumps(content, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        return ""


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
        llm = get_llm_with_tools()
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
            "tool_call_count": len(response.tool_calls),
        },
    )
    return response


async def _load_history(
    session: AsyncSession,
    conversation_id: UUID,
) -> list[BaseMessage]:
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None:
        raise ConversationNotFoundError("Conversation not found")

    result = await session.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(HISTORY_FETCH_LIMIT)
    )
    rows = list(result.all())
    rows.reverse()
    safe_rows = _select_safe_history_rows(rows)
    history = _rehydrate_messages(safe_rows)
    _validate_tool_protocol(history)

    # Do not hold the read transaction while waiting for Gemini or executing tools.
    await session.rollback()
    return history


async def _persist_successful_turn(
    session: AsyncSession,
    conversation_id: UUID,
    conversation_exists: bool,
    new_messages: list[BaseMessage],
) -> None:
    try:
        if not conversation_exists:
            session.add(Conversation(id=conversation_id))
        else:
            await session.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(updated_at=datetime.now(timezone.utc))
            )

        message_rows: list[Message] = []
        for message in new_messages:
            message_rows.append(
                Message(
                    conversation_id=conversation_id,
                    role=_message_role(message),
                    content_text=_stored_content_text(message),
                    message_payload=message_to_dict(message),
                )
            )
        session.add_all(message_rows)
        await session.commit()
    except Exception as exc:
        await session.rollback()
        raise ChatPersistenceError("Chat turn could not be persisted") from exc


async def _persist_tool_execution(
    session: AsyncSession,
    conversation_id: UUID,
    conversation_exists: bool,
    execution: ToolExecution,
) -> None:
    """Commit telemetry independently so failed model turns remain observable."""

    try:
        if not conversation_exists:
            session.add(Conversation(id=conversation_id))
        session.add(
            ToolCall(
                conversation_id=conversation_id,
                tool_call_id=execution.tool_call_id,
                tool_name=execution.tool_name,
                arguments=execution.arguments,
                result=execution.result,
                status=execution.status,
                duration_ms=execution.duration_ms,
            )
        )
        await session.commit()
    except Exception as exc:
        await session.rollback()
        raise ChatPersistenceError("Tool execution could not be recorded") from exc


async def generate_chat_reply(
    session: AsyncSession,
    message: str,
    conversation_id: UUID | None = None,
) -> ChatTurnResult:
    existing_conversation = conversation_id is not None
    target_conversation_id = conversation_id or uuid4()
    history = (
        await _load_history(session, target_conversation_id)
        if conversation_id is not None
        else []
    )

    human_message = HumanMessage(content=message)
    llm_messages: list[BaseMessage] = [
        SystemMessage(content=SYSTEM_PROMPT),
        *history,
        human_message,
    ]
    new_messages: list[BaseMessage] = [human_message]
    latest_search_products: list[dict[str, Any]] = []
    conversation_exists = existing_conversation

    for _ in range(MAX_TOOL_ITERATIONS):
        ai_message = await _invoke_llm(llm_messages, target_conversation_id)
        llm_messages.append(ai_message)
        new_messages.append(ai_message)

        if not ai_message.tool_calls:
            visible_text = _visible_text(ai_message)
            break

        for tool_call in ai_message.tool_calls:
            execution = await execute_tool(tool_call, session)
            await _persist_tool_execution(
                session=session,
                conversation_id=target_conversation_id,
                conversation_exists=conversation_exists,
                execution=execution,
            )
            conversation_exists = True
            tool_message = execution.to_message()
            llm_messages.append(tool_message)
            new_messages.append(tool_message)
            if execution.tool_name == "search_products" and execution.status == "success":
                latest_search_products = execution.products

        # Release every tool query transaction before the next external call.
        await session.rollback()
    else:
        raise ToolLoopLimitError("Gemini exceeded the maximum tool-call iterations")

    await _persist_successful_turn(
        session=session,
        conversation_id=target_conversation_id,
        conversation_exists=conversation_exists,
        new_messages=new_messages,
    )
    return ChatTurnResult(
        conversation_id=target_conversation_id,
        message=visible_text,
        products=latest_search_products,
    )
