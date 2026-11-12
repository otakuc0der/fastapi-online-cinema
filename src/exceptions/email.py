class BaseEmailError(Exception):
    """Base exception for email notification operations."""

    default_message = "An email notification error occurred."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(self.default_message if message is None else message)


class EmailDeliveryError(BaseEmailError):
    """An email could not be submitted to the SMTP server."""

    default_message = "Failed to send email."


class EmailTemplateError(BaseEmailError):
    """An email template could not be loaded or rendered."""

    default_message = "Failed to render email template."
