from app.security.passwords import hash_password, verify_password


def test_hash_password_never_returns_plaintext() -> None:
    """Password storage must be one-way and verifiable."""

    password_hash = hash_password("very-secure-password")

    assert password_hash != "very-secure-password"
    assert verify_password("very-secure-password", password_hash)
    assert not verify_password("wrong-password", password_hash)
