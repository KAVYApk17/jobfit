from uuid import uuid4

import pytest

from app.core.errors import Unauthorized
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_round_trip():
    hashed = hash_password("correct horse battery")
    assert hashed != "correct horse battery"
    assert verify_password(hashed, "correct horse battery")
    assert not verify_password(hashed, "wrong password")


def test_verify_rejects_garbage_hash():
    assert not verify_password("not-a-hash", "anything")


def test_token_round_trip():
    user_id = uuid4()
    assert decode_access_token(create_access_token(user_id)) == user_id


def test_expired_token_is_rejected():
    token = create_access_token(uuid4(), ttl_minutes=-1)
    with pytest.raises(Unauthorized, match="expired"):
        decode_access_token(token)


def test_tampered_token_is_rejected():
    token = create_access_token(uuid4())
    with pytest.raises(Unauthorized):
        decode_access_token(token[:-2] + "xx")
