import unittest
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch

from langchain_core.messages import AIMessage
from pydantic import ValidationError
from sqlalchemy import delete, select

from app.agent.model_router import ModelInvocationResult
from app.auth.passwords import hash_password, verify_password
from app.auth.sessions import (
    ExpiredSessionError,
    RevokedSessionError,
    UnknownSessionError,
    get_auth_context,
    hash_session_token,
)
from app.db.session import AsyncSessionLocal, engine
from app.models import AuthSession, Conversation, User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth import (
    DuplicateEmailError,
    InvalidCredentialsError,
    login_user,
    register_user,
    revoke_session,
)
from app.services.chat import (
    ConversationNotFoundError,
    _load_history,
    generate_chat_reply,
)


class AuthPureUnitTests(unittest.TestCase):
    def test_argon2id_hash_uses_required_parameters(self) -> None:
        password = "đây là một mật khẩu đủ dài"
        hashed = hash_password(password)

        self.assertTrue(hashed.startswith("$argon2id$"))
        self.assertIn("m=19456", hashed)
        self.assertIn("t=2", hashed)
        self.assertIn("p=1", hashed)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("a different password", hashed))
        self.assertNotIn(password, hashed)

    def test_password_policy_preserves_spaces_and_unicode(self) -> None:
        valid = "  mật khẩu có khoảng trắng  "
        self.assertEqual(RegisterRequest(email=" A@Example.COM ", password=valid).email, "a@example.com")
        self.assertEqual(LoginRequest(email="a@example.com", password=valid).password, valid)

        for length in (11, 129):
            with self.subTest(length=length):
                with self.assertRaises(ValidationError):
                    RegisterRequest(
                        email="a@example.com",
                        password="x" * length,
                    )

    def test_session_token_hash_is_sha256_and_not_raw_token(self) -> None:
        raw_token = "a-secure-opaque-token"
        token_hash = hash_session_token(raw_token)

        self.assertEqual(len(token_hash), 64)
        self.assertNotEqual(token_hash, raw_token)


class AuthDatabaseTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.db = AsyncSessionLocal()
        self.user_ids: list[UUID] = []
        self.conversation_ids: list[UUID] = []

    async def asyncTearDown(self) -> None:
        await self.db.rollback()
        if self.conversation_ids:
            await self.db.execute(
                delete(Conversation).where(Conversation.id.in_(self.conversation_ids))
            )
        if self.user_ids:
            await self.db.execute(delete(User).where(User.id.in_(self.user_ids)))
        await self.db.commit()
        await self.db.close()
        await engine.dispose()

    async def _register(self, email: str | None = None):
        result = await register_user(
            self.db,
            email=email or f"auth-{uuid4()}@example.com",
            password="a long enough password",
            display_name="Test user",
        )
        self.user_ids.append(result.user.id)
        return result

    async def test_registration_login_and_independent_sessions(self) -> None:
        registration = await self._register("  Test@Example.COM ")
        self.assertEqual(registration.user.email, "test@example.com")
        self.assertTrue(registration.user.password_hash.startswith("$argon2id$"))
        self.assertNotIn("a long enough password", registration.user.password_hash)

        stored_session = await self.db.scalar(
            select(AuthSession).where(AuthSession.id == registration.session.id)
        )
        self.assertIsNotNone(stored_session)
        assert stored_session is not None
        self.assertEqual(stored_session.token_hash, hash_session_token(registration.raw_token))
        self.assertNotEqual(stored_session.token_hash, registration.raw_token)

        login = await login_user(
            self.db,
            email="TEST@example.com",
            password="a long enough password",
        )
        self.assertNotEqual(login.raw_token, registration.raw_token)
        self.assertNotEqual(login.session.id, registration.session.id)

    async def test_duplicate_email_is_controlled(self) -> None:
        registration = await self._register()

        with self.assertRaises(DuplicateEmailError):
            await register_user(
                self.db,
                email=registration.user.email,
                password="a long enough password",
                display_name=None,
            )

    async def test_unknown_wrong_and_inactive_credentials_are_generic(self) -> None:
        registration = await self._register()
        user_id = registration.user.id

        for email, password in (
            (registration.user.email, "wrong password entirely"),
            (f"missing-{uuid4()}@example.com", "wrong password entirely"),
        ):
            with self.subTest(email=email):
                with self.assertRaises(InvalidCredentialsError) as context:
                    await login_user(self.db, email=email, password=password)
                self.assertEqual(str(context.exception), "Invalid email or password")

        await self.db.execute(
            User.__table__.update()
            .where(User.id == user_id)
            .values(is_active=False)
        )
        await self.db.commit()
        await self.db.refresh(registration.user)
        with self.assertRaises(InvalidCredentialsError) as context:
            await login_user(
                self.db,
                email=registration.user.email,
                password="a long enough password",
            )
        self.assertEqual(str(context.exception), "Invalid email or password")

    async def test_valid_expired_revoked_and_unknown_sessions(self) -> None:
        registration = await self._register()
        now = datetime.now(timezone.utc)
        context = await get_auth_context(self.db, registration.raw_token, now=now)
        self.assertEqual(context.user.id, registration.user.id)

        await revoke_session(self.db, context)
        with self.assertRaises(RevokedSessionError):
            await get_auth_context(self.db, registration.raw_token, now=now)

        expired = await self._register()
        await self.db.execute(
            AuthSession.__table__.update()
            .where(AuthSession.id == expired.session.id)
            .values(expires_at=now - timedelta(seconds=1))
        )
        await self.db.commit()
        await self.db.refresh(expired.session)
        with self.assertRaises(ExpiredSessionError):
            await get_auth_context(self.db, expired.raw_token, now=now)

        with self.assertRaises(UnknownSessionError):
            await get_auth_context(self.db, "random-invalid-token", now=now)

    async def test_owned_conversation_denies_other_users_and_anonymous_requesters(self) -> None:
        owner = await self._register()
        other = await self._register()
        conversation = Conversation(user_id=owner.user.id)
        self.db.add(conversation)
        await self.db.commit()
        self.conversation_ids.append(conversation.id)

        with self.assertRaises(ConversationNotFoundError):
            await _load_history(self.db, conversation.id, other.user.id)
        with self.assertRaises(ConversationNotFoundError):
            await _load_history(self.db, conversation.id, None)

        history = await _load_history(self.db, conversation.id, owner.user.id)
        self.assertEqual(history, [])

    async def test_new_conversation_records_authenticated_owner(self) -> None:
        registration = await self._register()
        invocation = ModelInvocationResult(
            message=AIMessage(content="A helpful answer"),
            model_id="test-model",
        )

        with patch(
            "app.services.chat._invoke_llm",
            new=AsyncMock(return_value=invocation),
        ):
            result = await generate_chat_reply(
                self.db,
                message="Help me choose a phone",
                user_id=registration.user.id,
            )

        self.conversation_ids.append(result.conversation_id)
        conversation = await self.db.scalar(
            select(Conversation).where(Conversation.id == result.conversation_id)
        )
        self.assertIsNotNone(conversation)
        assert conversation is not None
        self.assertEqual(conversation.user_id, registration.user.id)


if __name__ == "__main__":
    unittest.main()
