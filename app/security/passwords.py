import bcrypt


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt.

    Passwords are never stored directly. Bcrypt includes a salt in the final
    hash, which protects users even when two people choose the same password.
    """

    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""

    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
