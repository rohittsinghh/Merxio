from uuid import uuid4

from app.security.tokens import create_access_token, decode_access_token


def test_access_token_contains_user_identity() -> None:
    """The access token subject should round-trip back to the user id."""

    user_id = uuid4()
    token = create_access_token(user_id)

    assert decode_access_token(token) == user_id
