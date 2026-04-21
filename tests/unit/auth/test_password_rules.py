import pytest

from auth.password_rules import (
    PasswordMissingDigit,
    PasswordMissingUppercase,
    PasswordTooShort,
    validate,
)


def test_validate_rejects_short_password() -> None:
    with pytest.raises(PasswordTooShort):
        validate("Ab1")


def test_validate_rejects_password_without_digit() -> None:
    with pytest.raises(PasswordMissingDigit):
        validate("Password")


def test_validate_rejects_password_without_uppercase() -> None:
    with pytest.raises(PasswordMissingUppercase):
        validate("password1")


def test_validate_accepts_valid_password() -> None:
    validate("Password1")
