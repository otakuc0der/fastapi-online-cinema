class BaseAccountError(Exception):
    """Base exception for account operations."""

    default_message = "An account error occurred."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(
            self.default_message if message is None else message
        )


class UserGroupNotFoundError(BaseAccountError):
    """A required user group is missing from the database."""

    default_message = "Required user group was not found."


class UserAlreadyExistsError(BaseAccountError):
    """The provided email belongs to an existing account."""

    default_message = "A user with this email already exists."
