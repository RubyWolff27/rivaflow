"""Fernet-based encryption for storing OAuth tokens at rest."""

from cryptography.fernet import Fernet, InvalidToken

from rivaflow.core.settings import settings


def _get_fernet() -> Fernet:
    key = settings.WHOOP_ENCRYPTION_KEY
    if not key:
        raise ValueError(
            "WHOOP_ENCRYPTION_KEY is required for token encryption. "
            "Generate one with: python -c "
            '"from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"'
        )
    return Fernet(key.encode())


def encrypt_token(plaintext: str) -> str:
    """Encrypt a token string and return base64 ciphertext."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """Decrypt a ciphertext string back to plaintext.

    Raises:
        ValueError: If decryption fails (wrong key, corrupted data).
    """
    f = _get_fernet()
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except InvalidToken as e:
        raise ValueError("Failed to decrypt token — key may have changed") from e
