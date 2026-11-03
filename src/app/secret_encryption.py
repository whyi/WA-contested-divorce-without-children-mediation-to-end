import hashlib
import secrets

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def derive_encryption_key(secret: str | None) -> bytes:
    if not secret or len(secret.encode()) < 32:
        raise ValueError("AUTH_ENCRYPTION_KEY must contain at least 32 bytes.")
    return hashlib.sha256(secret.encode()).digest()


def encrypt_secret(value: bytes, key: bytes, associated_data: bytes | None = None) -> bytes:
    nonce = secrets.token_bytes(12)
    return nonce + AESGCM(key).encrypt(nonce, value, associated_data)


def decrypt_secret(
    ciphertext: bytes,
    key: bytes,
    associated_data: bytes | None = None,
) -> bytes:
    if len(ciphertext) < 13:
        raise ValueError("Encrypted secret is invalid.")
    try:
        return AESGCM(key).decrypt(ciphertext[:12], ciphertext[12:], associated_data)
    except InvalidTag as error:
        raise ValueError("Encrypted secret could not be authenticated.") from error
