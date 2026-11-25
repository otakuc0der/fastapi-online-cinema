class BaseMovieCommentError(Exception):
    """Base exception for movie comment operations."""

    default_message = "A movie comment error occurred."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(self.default_message if message is None else message)


class MovieCommentNotFoundError(BaseMovieCommentError):
    """The requested movie comment does not exist."""

    default_message = "Movie comment not found."


class MovieCommentPermissionError(BaseMovieCommentError):
    """The user cannot modify the requested movie comment."""

    default_message = "You don't have permission to modify this comment."
