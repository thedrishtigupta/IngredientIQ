"""Passwords and sign-in sessions.

Passwords: scrypt (Python standard library) with a random salt per user.
Sessions: a random token is given to the browser once; only its SHA-256 is stored,
so a leaked database cannot be used to sign in. The browser sends it as
"Authorization: Bearer <token>".
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
import time

from fastapi import Depends, Header, HTTPException

from src.api.db import get_repo, query_one

SESSION_DAYS = 30
_login_attempts: dict[str, list[float]] = {}
_N, _R, _P = 2**14, 8, 1  # scrypt cost: ~16 MB memory, a few tens of ms per hash


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt, digest = stored.split("$")
        if algo != "scrypt":
            return False
        check = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p), dklen=len(digest) // 2
        )
    except ValueError:
        return False
    return hmac.compare_digest(check.hex(), digest)


# Compared against when the email is unknown, so "no such user" takes as long as "wrong password".
_DUMMY_HASH = hash_password(secrets.token_hex(8))


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(repo, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    repo.connection.execute(
        "INSERT INTO user_sessions (token_hash, user_id, expires_at) VALUES (%s, %s, %s)",
        (_token_hash(token), user_id, expires),
    )
    # Housekeeping: drop this user's expired sessions.
    repo.connection.execute(
        "DELETE FROM user_sessions WHERE user_id = %s AND expires_at < now()", (user_id,)
    )
    return token


def delete_session(repo, token: str) -> None:
    repo.connection.execute("DELETE FROM user_sessions WHERE token_hash = %s", (_token_hash(token),))


def _bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    return token.strip() if scheme.lower() == "bearer" and token.strip() else None


def _user_for_token(repo, token: str | None):
    if not token:
        return None
    return query_one(
        repo,
        """SELECT u.user_id, u.email, u.display_name, u.created_at
           FROM user_sessions s JOIN users u USING (user_id)
           WHERE s.token_hash = %s AND s.expires_at > now()""",
        (_token_hash(token),),
    )


def optional_user(authorization: str | None = Header(None), repo=Depends(get_repo)):
    """The signed-in user, or None. Never fails: an expired token just means "signed out"."""
    return _user_for_token(repo, _bearer(authorization))


def current_user(authorization: str | None = Header(None), repo=Depends(get_repo)):
    """The signed-in user; 401 if there is none."""
    user = _user_for_token(repo, _bearer(authorization))
    if user is None:
        raise HTTPException(
            status_code=401, detail="Please sign in.", headers={"WWW-Authenticate": "Bearer"}
        )
    return user


def bearer_token(authorization: str | None = Header(None)) -> str | None:
    return _bearer(authorization)


def login_allowed(identifier: str, now: float | None = None) -> bool:
    """Small per-process guard suitable for Render Free; use edge/WAF limits too."""
    now = now or time.time()
    attempts = [t for t in _login_attempts.get(identifier, []) if now - t < 300]
    if len(attempts) >= 10:
        _login_attempts[identifier] = attempts
        return False
    attempts.append(now)
    _login_attempts[identifier] = attempts
    return True
