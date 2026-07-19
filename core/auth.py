"""Auth module - JWT + password hashing.

JWT_SECRET: env var JWT_SECRET (default = 'dev-secret-change-me').
Password hash: pbkdf2_sha256 (stdlib hashlib, no extra dep).
JWT: HS256 (stdlib hmac + hashlib + base64, no PyJWT dep).
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Optional


# --- Password hashing (pbkdf2_sha256) ---

_HASH_ITER = 200_000
_HASH_ALGO = "sha256"


def hash_password(password: str) -> str:
    """Hash password -> 'pbkdf2_sha256$<salt_b64>$<hash_b64>'."""
    salt = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac(_HASH_ALGO, password.encode("utf-8"), salt, _HASH_ITER)
    return f"pbkdf2_{_HASH_ALGO}${base64.b64encode(salt).decode()}${base64.b64encode(h).decode()}"


def verify_password(password: str, stored: str) -> bool:
    """Verify password against stored hash. Constant-time compare."""
    try:
        algo_part, salt_b64, hash_b64 = stored.split("$")
        if not algo_part.startswith("pbkdf2_"):
            return False
        algo = algo_part.split("_", 1)[1]
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
    except (ValueError, AttributeError):
        return False
    h = hashlib.pbkdf2_hmac(algo, password.encode("utf-8"), salt, _HASH_ITER)
    return hmac.compare_digest(h, expected)


# --- JWT (HS256) ---

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_TTL_SECONDS = int(os.getenv("JWT_TTL_SECONDS", "86400"))  # 24h


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    pad = 4 - len(data) % 4
    return base64.urlsafe_b64decode(data + ("=" * pad))


def create_jwt(user_id: str, role: str, ttl: Optional[int] = None) -> str:
    """Create JWT token. Payload: {sub, role, iat, exp}."""
    now = int(time.time())
    exp = now + (ttl or JWT_TTL_SECONDS)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": user_id, "role": role, "iat": now, "exp": exp}
    h = _b64url(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    signing = f"{h}.{p}".encode()
    sig = hmac.new(JWT_SECRET.encode(), signing, hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url(sig)}"


def decode_jwt(token: str) -> Optional[dict]:
    """Decode + verify JWT. Returns payload dict or None on invalid/expired."""
    try:
        h, p, s = token.split(".")
    except ValueError:
        return None
    signing = f"{h}.{p}".encode()
    expected = hmac.new(JWT_SECRET.encode(), signing, hashlib.sha256).digest()
    try:
        actual = _b64url_decode(s)
    except Exception:
        return None
    if not hmac.compare_digest(expected, actual):
        return None
    try:
        payload = json.loads(_b64url_decode(p))
    except Exception:
        return None
    if payload.get("exp", 0) < int(time.time()):
        return None
    return payload
