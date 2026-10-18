"""Hashing and checking of alarm codes. Codes are never stored in plain text."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any, Iterable, Mapping

from .const import CONF_CODE_HASH, CONF_CODE_SALT, CONF_DURESS_HASH, CONF_DURESS_SALT, PBKDF2_ITERATIONS


def hash_code(code: str, salt: str | None = None) -> tuple[str, str]:
    """Return (hash, salt) as hex strings. CPU-heavy: call from an executor."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", code.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS
    )
    return digest.hex(), salt


def code_matches(code: str, data: Mapping[str, Any]) -> bool:
    stored = data.get(CONF_CODE_HASH)
    salt = data.get(CONF_CODE_SALT)
    if not stored or not salt:
        return False
    digest, _ = hash_code(code, salt)
    return hmac.compare_digest(digest, stored)


def find_user_by_code(code: str, users: Iterable[Any]) -> Any | None:
    """`users` are objects with a `.data` mapping. CPU-heavy: call from an executor."""
    found = None
    for user in users:  # no early exit: keep timing independent of the position
        if code_matches(code, user.data) and found is None:
            found = user
    return found


def duress_matches(code: str, data: Mapping[str, Any]) -> bool:
    return code_matches(code, {CONF_CODE_HASH: data.get(CONF_DURESS_HASH), CONF_CODE_SALT: data.get(CONF_DURESS_SALT)})


def find_user_and_kind(code: str, users: Iterable[Any]) -> tuple[Any | None, bool]:
    """Who the code belongs to, and whether it is that user's duress code. CPU-heavy: call from an executor.
    Both codes of every user are always checked, so the time does not tell which one it was."""
    found: Any | None = None
    duress = False
    for user in users:
        normal = code_matches(code, user.data)
        under_duress = duress_matches(code, user.data)
        if (normal or under_duress) and found is None:
            found, duress = user, under_duress and not normal
    return found, duress
