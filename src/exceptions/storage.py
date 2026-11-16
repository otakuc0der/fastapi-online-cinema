class BaseS3Error(Exception):
    """Base exception for S3 storage operations."""

    default_message = "An S3 storage error occurred."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(self.default_message if message is None else message)


class S3ConnectionError(BaseS3Error):
    """Raised when connecting to S3 storage fails."""

    default_message = "Failed to connect to S3 storage."


class S3FileUploadError(BaseS3Error):
    """Raised when uploading a file to S3 storage fails."""

    default_message = "Failed to upload file to S3."


class S3FileDeleteError(BaseS3Error):
    """Raised when deleting a file from S3 storage fails."""

    default_message = "Failed to delete file from S3."
