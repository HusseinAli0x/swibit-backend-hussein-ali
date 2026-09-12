"""Password hashing and JWT access-token helpers.

Uses `bcrypt` directly rather than through passlib: passlib 1.7.4's bcrypt
backend self-test breaks under bcrypt>=4.1 (it no longer exposes
`__about__.__version__`, and no longer silently truncates >72-byte inputs).
bcrypt's own 72-byte secret limit is enforced explicitly below instead.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

_BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    secret = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(secret, bcrypt.gensalt()).decode("ascii")


def verify_password(plain_password: str, password_hash: str) -> bool:
    secret = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(secret, password_hash.encode("ascii"))
    except ValueError:
        return False


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT whose `sub` claim identifies the user (their id, as a string)."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> str | None:
    """Return the `sub` claim if the token is valid and unexpired, else None."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None
