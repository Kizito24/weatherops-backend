"""Password hashing and verification utilities."""

from passlib.context import CryptContext

# Configure argon2 password hashing (with bcrypt fallback for backwards compatibility)
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="bcrypt",
)


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Args:
        password: Plaintext password to hash.

    Returns:
        Hashed password string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a hash.

    Args:
        plain_password: Plaintext password to verify.
        hashed_password: Hashed password from database.

    Returns:
        True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)
