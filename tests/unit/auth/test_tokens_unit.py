from datetime import datetime, timezone

import pytest

from auth.tokens import TokenError, _to_datetime, create_access_token, create_refresh_token, decode_access_token, decode_refresh_token


def test_roundtrip_access_token() -> None:
    token = create_access_token("user-1")
    payload = decode_access_token(token)
    assert payload.subject == "user-1"
    assert payload.token_type == "access"


def test_roundtrip_refresh_token() -> None:
    token = create_refresh_token("user-1")
    payload = decode_refresh_token(token)
    assert payload.subject == "user-1"
    assert payload.token_type == "refresh"


def test_rejects_wrong_token_type() -> None:
    token = create_refresh_token("user-1")
    with pytest.raises(TokenError):
        decode_access_token(token)


def test_to_datetime_from_numeric_timestamp() -> None:
    value = _to_datetime(1_700_000_000)
    assert value.tzinfo == timezone.utc


def test_to_datetime_from_naive_datetime() -> None:
    value = _to_datetime(datetime(2024, 1, 1, 12, 0, 0))
    assert value.tzinfo == timezone.utc
