import unittest

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
    message_to_dict,
    messages_from_dict,
)
from pydantic import ValidationError

from app.agent.model_router import (
    MODEL_PRIORITY,
    AllModelsRateLimitedError,
    ModelAuthenticationError,
    ModelInvocationError,
    ModelRouter,
    ModelSpec,
    RollingWindowRateLimiter,
    _ModelState,
    tool_history_family,
)
from app.agent.tool_executor import execute_tool
from app.agent.tools.search_products import SearchProductsInput


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value


class FakeClient:
    def __init__(self, model_id: str, calls: list[str], error: Exception | None = None) -> None:
        self.model_id = model_id
        self.calls = calls
        self.error = error

    async def ainvoke(self, messages: list[HumanMessage]) -> AIMessage:
        self.calls.append(self.model_id)
        if self.error is not None:
            raise self.error
        return AIMessage(content="ok")


def make_router(
    clock: FakeClock,
    specs: tuple[ModelSpec, ...],
    calls: list[str],
    errors: dict[str, Exception] | None = None,
) -> ModelRouter:
    errors = errors or {}
    clients = {
        spec.model_id: FakeClient(spec.model_id, calls, errors.get(spec.model_id))
        for spec in specs
    }
    return ModelRouter(
        specs,
        client_factory=lambda model_id: clients[model_id],
        tool_client_factory=lambda model_id: clients[model_id],
        clock=clock,
    )


def tool_history(model_name: str) -> list[AIMessage | ToolMessage]:
    ai_message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "get_test_value",
                "args": {"value": "ok"},
                "id": "tool-call-1",
                "type": "tool_call",
            }
        ],
        response_metadata={"model_name": model_name},
    )
    return [
        ai_message,
        ToolMessage(
            content='{"value":"ok"}',
            tool_call_id="tool-call-1",
            name="get_test_value",
        ),
    ]


TOOL_MODEL_SPECS = tuple(
    ModelSpec(model_id, 1)
    for model_id in (
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemma-4-31b-it",
        "gemma-4-26b-a4b-it",
    )
)


class ModelRouterTests(unittest.IsolatedAsyncioTestCase):
    async def test_registry_preserves_priority_and_rpm(self) -> None:
        self.assertEqual(
            [(spec.model_id, spec.rpm) for spec in MODEL_PRIORITY],
            [
                ("gemini-3.5-flash-lite", 15),
                ("gemini-3.1-flash-lite", 15),
                ("gemma-4-31b-it", 30),
                ("gemma-4-26b-a4b-it", 30),
            ],
        )

    async def test_limiter_retry_after_is_zero_until_exhausted(self) -> None:
        clock = FakeClock()
        limiter = RollingWindowRateLimiter(2, clock=clock)

        self.assertEqual(await limiter.retry_after(), 0)
        self.assertTrue(await limiter.try_reserve())
        self.assertEqual(await limiter.retry_after(), 0)
        self.assertTrue(await limiter.try_reserve())
        self.assertEqual(await limiter.retry_after(), 60)

        clock.value = 10
        self.assertEqual(await limiter.retry_after(), 50)
        clock.value = 60
        self.assertEqual(await limiter.retry_after(), 0)

    async def test_model_state_uses_the_larger_of_two_blockers(self) -> None:
        clock = FakeClock()
        state = _ModelState(ModelSpec("test", 1), clock)
        state.limiter.window_seconds = 20
        self.assertTrue(await state.limiter.try_reserve())
        await state.mark_cooldown(10)

        self.assertEqual(await state.retry_after(), 20)

        fresh_state = _ModelState(ModelSpec("fresh", 1), clock)
        await fresh_state.mark_cooldown(5)
        self.assertEqual(await fresh_state.retry_after(), 5)

    async def test_global_retry_after_uses_earliest_usable_model(self) -> None:
        clock = FakeClock()
        specs = tuple(ModelSpec(model_id, 1) for model_id in ("a", "b", "c", "d"))
        calls: list[str] = []
        router = make_router(clock, specs, calls)

        await router._states["a"].mark_cooldown(5)
        router._states["b"].limiter._timestamps.append(-20)  # wait 40 seconds
        router._states["c"].limiter._timestamps.append(-30)  # wait 30 seconds
        router._states["d"].limiter._timestamps.append(-40)  # wait 20 seconds

        with self.assertRaises(AllModelsRateLimitedError) as context:
            await router.ainvoke_with_fallback([HumanMessage(content="hello")])
        self.assertEqual(context.exception.retry_after, 5)
        self.assertEqual(calls, [])

    async def test_priority_uses_first_available_model(self) -> None:
        specs = tuple(ModelSpec(model_id, 1) for model_id in ("a", "b", "c", "d"))

        scenarios = (
            ([], "a"),
            (["a"], "b"),
            (["a", "b"], "c"),
            (["a", "b", "c"], "d"),
        )
        for exhausted, expected in scenarios:
            with self.subTest(exhausted=exhausted):
                clock = FakeClock()
                calls: list[str] = []
                router = make_router(clock, specs, calls)
                for model_id in exhausted:
                    self.assertTrue(await router._states[model_id].limiter.try_reserve())

                result = await router.ainvoke_with_fallback(
                    [HumanMessage(content="hello")]
                )
                self.assertEqual(result.model_id, expected)
                self.assertEqual(calls, [expected])

    async def test_tool_history_family_uses_response_metadata(self) -> None:
        self.assertIsNone(tool_history_family([HumanMessage(content="hello")]))
        self.assertEqual(
            tool_history_family(tool_history("gemini-3.5-flash-lite")),
            "gemini",
        )
        self.assertEqual(
            tool_history_family(tool_history("gemma-4-31b-it")),
            "gemma",
        )

        restored = messages_from_dict(
            [message_to_dict(message) for message in tool_history("gemini-3.5-flash-lite")]
        )
        self.assertEqual(tool_history_family(restored), "gemini")

    async def test_gemini_tool_history_excludes_gemma_models(self) -> None:
        clock = FakeClock()
        calls: list[str] = []
        router = make_router(clock, TOOL_MODEL_SPECS, calls)

        result = await router.ainvoke_with_fallback(tool_history("gemini-3.5-flash-lite"))
        self.assertEqual(result.model_id, "gemini-3.5-flash-lite")
        self.assertEqual(calls, ["gemini-3.5-flash-lite"])

    async def test_gemini_tool_history_falls_back_to_3_1_only(self) -> None:
        clock = FakeClock()
        calls: list[str] = []
        router = make_router(clock, TOOL_MODEL_SPECS, calls)
        await router._states["gemini-3.5-flash-lite"].limiter.try_reserve()

        result = await router.ainvoke_with_fallback(tool_history("gemini-3.5-flash-lite"))
        self.assertEqual(result.model_id, "gemini-3.1-flash-lite")
        self.assertEqual(calls, ["gemini-3.1-flash-lite"])

    async def test_gemini_tool_history_does_not_fallback_to_gemma(self) -> None:
        clock = FakeClock()
        calls: list[str] = []
        router = make_router(clock, TOOL_MODEL_SPECS, calls)
        for model_id in ("gemini-3.5-flash-lite", "gemini-3.1-flash-lite"):
            await router._states[model_id].limiter.try_reserve()

        with self.assertRaises(AllModelsRateLimitedError) as context:
            await router.ainvoke_with_fallback(tool_history("gemini-3.5-flash-lite"))
        self.assertEqual(context.exception.retry_after, 60)
        self.assertEqual(calls, [])

    async def test_gemma_tool_history_stays_with_gemma_family(self) -> None:
        clock = FakeClock()
        calls: list[str] = []
        router = make_router(clock, TOOL_MODEL_SPECS, calls)

        result = await router.ainvoke_with_fallback(tool_history("gemma-4-31b-it"))
        self.assertEqual(result.model_id, "gemma-4-31b-it")
        self.assertEqual(calls, ["gemma-4-31b-it"])

        calls.clear()
        self.assertFalse(await router._states["gemma-4-31b-it"].limiter.try_reserve())
        result = await router.ainvoke_with_fallback(tool_history("gemma-4-31b-it"))
        self.assertEqual(result.model_id, "gemma-4-26b-a4b-it")
        self.assertEqual(calls, ["gemma-4-26b-a4b-it"])

    async def test_unidentified_tool_history_fails_closed(self) -> None:
        clock = FakeClock()
        calls: list[str] = []
        router = make_router(clock, TOOL_MODEL_SPECS, calls)
        history = tool_history("provider-without-a-supported-family")

        with self.assertRaises(ModelInvocationError):
            await router.ainvoke_with_fallback(history)
        self.assertEqual(calls, [])

    async def test_retry_after_uses_only_eligible_tool_history_models(self) -> None:
        clock = FakeClock()
        calls: list[str] = []
        router = make_router(clock, TOOL_MODEL_SPECS, calls)
        router._states["gemini-3.5-flash-lite"].limiter._timestamps.append(-40)
        router._states["gemini-3.1-flash-lite"].limiter._timestamps.append(-52)

        with self.assertRaises(AllModelsRateLimitedError) as context:
            await router.ainvoke_with_fallback(tool_history("gemini-3.5-flash-lite"))
        self.assertEqual(context.exception.retry_after, 8)
        self.assertEqual(calls, [])

    async def test_provider_rate_limit_falls_back_and_enters_cooldown(self) -> None:
        specs = tuple(ModelSpec(model_id, 1) for model_id in ("a", "b"))
        calls: list[str] = []

        class RateLimitError(Exception):
            status_code = 429

        router = make_router(
            FakeClock(),
            specs,
            calls,
            errors={"a": RateLimitError()},
        )
        result = await router.ainvoke_with_fallback([HumanMessage(content="hello")])
        self.assertEqual(result.model_id, "b")
        self.assertEqual(calls, ["a", "b"])
        self.assertGreater(await router._states["a"].retry_after(), 0)

    async def test_authentication_error_does_not_try_lower_priority_models(self) -> None:
        specs = tuple(ModelSpec(model_id, 1) for model_id in ("a", "b", "c"))
        calls: list[str] = []

        class AuthenticationError(Exception):
            status_code = 401

        router = make_router(
            FakeClock(),
            specs,
            calls,
            errors={"a": AuthenticationError()},
        )
        with self.assertRaises(ModelAuthenticationError):
            await router.ainvoke_with_fallback([HumanMessage(content="hello")])
        self.assertEqual(calls, ["a"])

    async def test_all_models_exhausted_raises_controlled_error(self) -> None:
        specs = tuple(ModelSpec(model_id, 1) for model_id in ("a", "b", "c"))
        calls: list[str] = []
        router = make_router(FakeClock(), specs, calls)
        for spec in specs:
            self.assertTrue(await router._states[spec.model_id].limiter.try_reserve())

        with self.assertRaises(AllModelsRateLimitedError) as context:
            await router.ainvoke_with_fallback([HumanMessage(content="hello")])
        self.assertEqual(context.exception.retry_after, 60)
        self.assertEqual(calls, [])


class SearchProductsValidationTests(unittest.IsolatedAsyncioTestCase):
    async def test_impossible_price_range_is_invalid_arguments_without_db_call(self) -> None:
        with self.assertRaises(ValidationError):
            SearchProductsInput.model_validate(
                {"min_price": 20_000_000, "max_price": 10_000_000}
            )

        execution = await execute_tool(
            {
                "id": "invalid-price-range",
                "name": "search_products",
                "args": {"min_price": 20_000_000, "max_price": 10_000_000},
            },
            object(),
        )
        self.assertEqual(execution.status, "error")
        self.assertEqual(execution.result["error"], "invalid_arguments")


if __name__ == "__main__":
    unittest.main()
