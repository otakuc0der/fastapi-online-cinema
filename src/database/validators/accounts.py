import re

from email_validator import (
    EmailNotValidError,
    validate_email as validate_email_address,
)


def validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")

    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")

    if not re.search(r"[0-9]", password):
        raise ValueError("Password must contain at least one digit.")

    if not re.search(r"[@$!%*?&#]", password):
        raise ValueError(
            "Password must contain at least one special character: "
            "@, $, !, %, *, ?, #, &."
        )

    return password


def validate_email(user_email: str) -> str:
    normalized_input = user_email.strip().lower()

    try:
        result = validate_email_address(
            normalized_input,
            check_deliverability=False,
        )
    except EmailNotValidError as error:
        raise ValueError(str(error)) from error

    return result.normalized
