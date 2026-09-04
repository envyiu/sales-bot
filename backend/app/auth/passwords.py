from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from pwdlib.hashers.argon2 import Argon2Hasher


PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128
ARGON2_MEMORY_COST = 19_456
ARGON2_TIME_COST = 2
ARGON2_PARALLELISM = 1

password_hash = PasswordHash(
    (
        Argon2Hasher(
            memory_cost=ARGON2_MEMORY_COST,
            time_cost=ARGON2_TIME_COST,
            parallelism=ARGON2_PARALLELISM,
        ),
    )
)

# This hash was generated once with the same Argon2id parameters and is reused
# for unknown emails, so the missing-user path still performs password
# verification work. It is not a credential and must never be returned/logged.
DUMMY_PASSWORD_HASH = (
    "$argon2id$v=19$m=19456,t=2,p=1$Ce8fQlL45vl9x+Icd4FL1A$"
    "9xqapQj7ZgIH3CCAIHc2kddha40F2RSkebHeBqIPafQ"
)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(password, hashed_password)
    except (TypeError, ValueError, UnknownHashError):
        return False
