class PasswordTooShort(ValueError):
    pass


class PasswordMissingDigit(ValueError):
    pass


class PasswordMissingUppercase(ValueError):
    pass


def validate(password: str) -> None:
    if len(password) < 8:
        raise PasswordTooShort("Password must be at least 8 characters long")
    if not any(character.isdigit() for character in password):
        raise PasswordMissingDigit("Password must include at least one digit")
    if not any(character.isupper() for character in password):
        raise PasswordMissingUppercase("Password must include at least one uppercase letter")
