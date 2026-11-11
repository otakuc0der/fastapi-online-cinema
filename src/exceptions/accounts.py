class BaseAccountError(Exception):
    """Base exception for account operations."""

    default_message = "An account error occurred."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(self.default_message if message is None else message)


class UserGroupNotFoundError(BaseAccountError):
    """A required user group is missing from the database."""

    default_message = "Required user group was not found."


class UserAlreadyExistsError(BaseAccountError):
    """The provided email belongs to an existing account."""

    default_message = "A user with this email already exists."


class InvalidActivationTokenError(BaseAccountError):
    """The activation token is invalid, expired or belongs to another account."""

    default_message = "Invalid or expired activation token."


class UserAlreadyActiveError(BaseAccountError):
    """The account has already been activated."""

    default_message = "User account is already active."


class InvalidCredentialsError(BaseAccountError):
    """The supplied login credentials are incorrect."""

    default_message = "Invalid email or password."


class UserNotActiveError(BaseAccountError):
    """The requested operation requires an active account."""

    default_message = "User account is not activated."


class InvalidPasswordError(BaseAccountError):
    """The supplied current password is incorrect."""

    default_message = "Current password is incorrect."


class PasswordUnchangedError(BaseAccountError):
    """The new password matches the current password."""

    default_message = "New password must differ from the current password."


class UserNotFoundError(BaseAccountError):
    """The requested user does not exist."""

    default_message = "User was not found."
