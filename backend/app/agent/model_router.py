import asyncio
import logging
import math
import time
from collections import deque
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from uuid import UUID

from google.genai.errors import APIError, ClientError, ServerError
from langchain_core.messages import AIMessage, BaseMessage

from app.agent.llm import LLMConfigurationError, get_llm, get_llm_with_tools
from app.agent.tools import TOOLS


logger = logging.getLogger(__name__)
MODEL_COOLDOWN_SECONDS = 60


@dataclass(frozen=True, slots=True)
class ModelSpec:
    model_id: str
    rpm: int


MODEL_PRIORITY: tuple[ModelSpec, ...] = (
    ModelSpec("gemini-3.5-flash-lite", 15),
    ModelSpec("gemini-3.1-flash-lite", 15),
    ModelSpec("gemma-4-31b-it", 30),
    ModelSpec("gemma-4-26b-a4b-it", 30),
)


@dataclass(frozen=True, slots=True)
class ModelInvocationResult:
    message: AIMessage
    model_id: str


class ModelRouterError(RuntimeError):
    """Base error raised by the model router."""


class ModelAuthenticationError(ModelRouterError):
    """Raised when the shared Google credential is not accepted."""


class ModelTemporaryError(ModelRouterError):
    """Raised for provider availability failures that are not rate limits."""


class ModelInvocationError(ModelRouterError):
    """Raised for non-retryable model invocation failures."""


class AllModelsRateLimitedError(ModelRouterError):
    """Raised when every model is blocked by local or provider rate limits."""

    def __init__(self, retry_after: int) -> None:
        self.retry_after = max(1, retry_after)
        super().__init__("All configured Gemini models are rate-limited")


class RollingWindowRateLimiter:
    """Concurrency-safe in-memory rolling-window request limiter."""

    def __init__(
        self,
        rpm: int,
        *,
        window_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if rpm < 1:
            raise ValueError("rpm must be positive")
        self.rpm = rpm
        self.window_seconds = window_seconds
        self._clock = clock
        self._timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    def _prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._timestamps and self._timestamps[0] <= cutoff:
            self._timestamps.popleft()

    async def try_reserve(self) -> bool:
        """Atomically reserve a request slot if one is available."""

        async with self._lock:
            now = self._clock()
            self._prune(now)
            if len(self._timestamps) >= self.rpm:
                return False
            self._timestamps.append(now)
            return True

    async def retry_after(self) -> int:
        async with self._lock:
            now = self._clock()
            self._prune(now)
            if len(self._timestamps) < self.rpm:
                return 0
            return max(
                1,
                math.ceil(self._timestamps[0] + self.window_seconds - now),
            )


class _ModelState:
    def __init__(self, spec: ModelSpec, clock: Callable[[], float]) -> None:
        self.spec = spec
        self.limiter = RollingWindowRateLimiter(spec.rpm, clock=clock)
        self._clock = clock
        self._cooldown_until = 0.0
        self._lock = asyncio.Lock()

    async def reserve(self) -> str:
        """Return allowed/local_rpm_exhausted/provider_cooldown atomically."""

        async with self._lock:
            now = self._clock()
            if self._cooldown_until > now:
                return "provider_cooldown"
            if not await self.limiter.try_reserve():
                return "local_rpm_exhausted"
            return "allowed"

    async def mark_cooldown(self, seconds: int) -> None:
        async with self._lock:
            self._cooldown_until = max(
                self._cooldown_until,
                self._clock() + max(1, seconds),
            )

    async def retry_after(self) -> int:
        async with self._lock:
            now = self._clock()
            cooldown_wait = max(0, math.ceil(self._cooldown_until - now))
            limiter_wait = await self.limiter.retry_after()
            return max(cooldown_wait, limiter_wait)


ClientFactory = Callable[[str], Any]


class ModelRouter:
    def __init__(
        self,
        specs: Sequence[ModelSpec] = MODEL_PRIORITY,
        *,
        client_factory: ClientFactory = get_llm,
        tool_client_factory: ClientFactory = get_llm_with_tools,
        clock: Callable[[], float] = time.monotonic,
        cooldown_seconds: int = MODEL_COOLDOWN_SECONDS,
    ) -> None:
        self.specs = tuple(specs)
        self._client_factory = client_factory
        self._tool_client_factory = tool_client_factory
        self._clock = clock
        self._cooldown_seconds = cooldown_seconds
        self._states = {
            spec.model_id: _ModelState(spec, clock) for spec in self.specs
        }

    def _client_for(
        self,
        model_id: str,
        tools: Sequence[Any] | None,
    ) -> Any:
        if tools is None:
            return self._client_factory(model_id)
        if tools is TOOLS:
            return self._tool_client_factory(model_id)
        return self._client_factory(model_id).bind_tools(tools)

    @staticmethod
    def _status_code(exc: Exception) -> int | None:
        for attribute in ("status_code", "code", "status"):
            value = getattr(exc, attribute, None)
            if isinstance(value, int):
                return value
            if isinstance(value, str) and value.isdigit():
                return int(value)
        return None

    @staticmethod
    def _provider_status(exc: Exception) -> str:
        response_json = getattr(exc, "response_json", None)
        if not isinstance(response_json, dict):
            return ""
        error = response_json.get("error")
        if not isinstance(error, dict):
            return ""
        return str(error.get("status", "")).upper()

    @classmethod
    def _classify_provider_error(cls, exc: Exception) -> str:
        code = cls._status_code(exc)
        provider_status = cls._provider_status(exc)
        error_name = type(exc).__name__.lower()

        if code == 429 or provider_status in {
            "RESOURCE_EXHAUSTED",
            "RATE_LIMIT_EXCEEDED",
        } or error_name in {"resourceexhausted", "ratelimiterror", "toomanyrequests"}:
            return "rate_limit"

        if code in {401, 403} or provider_status in {
            "UNAUTHENTICATED",
            "PERMISSION_DENIED",
        } or error_name in {"authenticationerror", "unauthenticated"}:
            return "authentication"

        if isinstance(exc, ServerError) or (code is not None and code >= 500):
            return "temporary"

        # The Gemini API can report an invalid key as a 400 INVALID_ARGUMENT.
        # Keep this narrow marker as a compatibility fallback for wrapped errors.
        if "api key not valid" in str(exc).lower():
            return "authentication"

        if isinstance(exc, (APIError, ClientError)):
            return "invocation"
        return "invocation"

    @staticmethod
    def _retry_after_from(exc: Exception) -> int | None:
        for attribute in ("retry_after", "retry_after_seconds"):
            value = getattr(exc, attribute, None)
            if isinstance(value, (int, float)) and value > 0:
                return max(1, math.ceil(value))
        return None

    async def _log_skip(
        self,
        spec: ModelSpec,
        reason: str,
        conversation_id: UUID | None,
    ) -> None:
        logger.info(
            "llm_model_skipped",
            extra={
                "event": "llm_model_skipped",
                "conversation_id": str(conversation_id) if conversation_id else None,
                "model": spec.model_id,
                "reason": reason,
            },
        )

    async def ainvoke_with_fallback(
        self,
        messages: list[BaseMessage],
        *,
        conversation_id: UUID | None = None,
        tools: Sequence[Any] | None = None,
    ) -> ModelInvocationResult:
        for index, spec in enumerate(self.specs):
            state = self._states[spec.model_id]
            reservation = await state.reserve()
            if reservation != "allowed":
                await self._log_skip(spec, reservation, conversation_id)
                continue

            try:
                client = self._client_for(spec.model_id, tools)
                response = await client.ainvoke(messages)
            except LLMConfigurationError:
                raise
            except Exception as exc:
                classification = self._classify_provider_error(exc)
                if classification == "rate_limit":
                    cooldown = self._retry_after_from(exc) or self._cooldown_seconds
                    await state.mark_cooldown(cooldown)
                    if index + 1 < len(self.specs):
                        logger.warning(
                            "llm_fallback",
                            extra={
                                "event": "llm_fallback",
                                "conversation_id": (
                                    str(conversation_id) if conversation_id else None
                                ),
                                "from_model": spec.model_id,
                                "to_model": self.specs[index + 1].model_id,
                                "reason": "rate_limit",
                            },
                        )
                    continue
                if classification == "authentication":
                    raise ModelAuthenticationError("Gemini authentication failed") from exc
                if classification == "temporary":
                    raise ModelTemporaryError("Gemini is temporarily unavailable") from exc
                raise ModelInvocationError("Gemini request failed") from exc

            if not isinstance(response, AIMessage):
                raise ModelInvocationError("Gemini returned an unexpected message type")

            logger.info(
                "llm_call",
                extra={
                    "event": "llm_call",
                    "conversation_id": str(conversation_id) if conversation_id else None,
                    "model": spec.model_id,
                    "status": "success",
                },
            )
            return ModelInvocationResult(message=response, model_id=spec.model_id)

        waits = [
            wait
            for wait in [await state.retry_after() for state in self._states.values()]
            if wait > 0
        ]
        retry_after = min(waits or [1])
        raise AllModelsRateLimitedError(retry_after)


@lru_cache(maxsize=1)
def get_model_router() -> ModelRouter:
    return ModelRouter()
