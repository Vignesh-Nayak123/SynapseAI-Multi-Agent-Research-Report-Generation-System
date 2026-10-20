from __future__ import annotations

import base64
import os
from typing import Tuple

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes

PBKDF2_ITERATIONS = 600000
AES_KEY_LENGTH = 32  # AES-256
SALT_LENGTH = 16
IV_LENGTH = 12


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES-GCM key from passphrase + salt via PBKDF2-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=AES_KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def decrypt_api_key(
    encrypted_b64: str,
    iv_b64: str,
    salt_b64: str,
    passphrase: str,
) -> str:
    """
    Decrypt an API key that was encrypted client-side with the same PBKDF2+AES-GCM scheme.

    The decrypted string is returned, and the caller is responsible for clearing
    it from memory via `wipe_string` after use.
    """
    try:
        encrypted = base64.b64decode(encrypted_b64)
        iv = base64.b64decode(iv_b64)
        salt = base64.b64decode(salt_b64)
    except Exception as exc:
        raise ValueError("Invalid base64-encoded encryption fields") from exc

    key = _derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(iv, encrypted, None)
    except Exception as exc:
        raise ValueError("Decryption failed — incorrect passphrase or corrupted data") from exc

    return plaintext.decode("utf-8")


def encrypt_trace_data(
    plaintext: str,
    passphrase: str,
    salt: bytes | None = None,
) -> Tuple[str, str]:
    """
    Encrypt trace data (prompts, responses, reports) for storage at rest.

    Returns (ciphertext_b64, salt_b64).
    The IV is prepended to the ciphertext and extracted on decrypt.
    When ``salt`` is provided (e.g. the session ``encryption_salt``), it is
    reused so decryption with the session salt succeeds; otherwise a fresh
    random salt is generated.
    """
    if salt is None:
        salt = os.urandom(SALT_LENGTH)
    iv = os.urandom(IV_LENGTH)
    key = _derive_key(passphrase, salt)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)

    # Prepend the IV to the ciphertext so we can decrypt without needing it separately
    combined = iv + ciphertext
    return base64.b64encode(combined).decode("ascii"), base64.b64encode(salt).decode("ascii")


def decrypt_trace_data(
    encrypted_b64: str,
    salt_b64: str,
    passphrase: str,
) -> str:
    """
    Decrypt trace data that was encrypted with encrypt_trace_data.
    """
    try:
        combined = base64.b64decode(encrypted_b64)
        salt = base64.b64decode(salt_b64)
    except Exception as exc:
        raise ValueError("Invalid base64-encoded trace data") from exc

    iv = combined[:IV_LENGTH]
    ciphertext = combined[IV_LENGTH:]

    key = _derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(iv, ciphertext, None)
    except Exception as exc:
        raise ValueError("Trace decryption failed — incorrect passphrase or corrupted data") from exc

    return plaintext.decode("utf-8")


# Note: Python strings are immutable, so true memory-wipe is not possible.
# We rely on garbage collection + never persisting the passphrase to disk.
# The caller should delete references (del var) after use to minimize exposure.
