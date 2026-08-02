"""Symmetric encryption for provider credentials at rest (Fernet)."""

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


class CredentialDecryptionError(Exception):
    pass


def _fernet() -> Fernet:
    return Fernet(get_settings().credential_encryption_key.encode("utf-8"))


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise CredentialDecryptionError("stored credential could not be decrypted") from exc
