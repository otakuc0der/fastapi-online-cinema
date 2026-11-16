class BaseProfileError(Exception):
    """Base exception for profile operations."""

    default_message = "A profile error occurred."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(self.default_message if message is None else message)


class UserProfileAlreadyExistsError(BaseProfileError):
    """The user already has a profile."""

    default_message = "User already has a profile."
