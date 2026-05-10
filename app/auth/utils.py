"""
Authentication utilities: password hashing, API key generation.
"""
import secrets
import hashlib
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_api_key() -> str:
    """
    Generate a secure random API key.
    Returns a 64-character hex string.
    """
    return secrets.token_hex(32)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for storage.
    Uses SHA-256 for fast comparison.
    """
    return hashlib.sha256(api_key.encode()).hexdigest()
