from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm import LLMConfigurationError
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import (
    ChatHistoryError,
    ChatPersistenceError,
    ChatProviderAuthenticationError,
    ChatProviderError,
    ChatProviderRateLimitError,
    ChatProviderTemporaryError,
    ConversationNotFoundError,
    InvalidChatResponseError,
    generate_chat_reply,
)


router = APIRouter()


@router.post("", response_model=ChatResponse, summary="Send a message to Gemini")
async def create_chat_message(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_db),
) -> ChatResponse:
    try:
        conversation_id, response_text = await generate_chat_reply(
            session=session,
            message=payload.message,
            conversation_id=payload.conversation_id,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from exc
    except ChatHistoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Conversation history could not be loaded",
        ) from exc
    except LLMConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat provider is not configured",
        ) from exc
    except ChatProviderAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Chat provider authentication failed",
        ) from exc
    except ChatProviderRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Chat provider rate limit reached",
            headers={"Retry-After": "30"},
        ) from exc
    except ChatProviderTemporaryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat provider is temporarily unavailable",
        ) from exc
    except InvalidChatResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Chat provider returned no visible response",
        ) from exc
    except ChatPersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat response could not be saved",
        ) from exc
    except ChatProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Chat provider request failed",
        ) from exc

    return ChatResponse(conversation_id=conversation_id, message=response_text)
