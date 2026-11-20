class BaseMovieError(Exception):
    """Base exception for movie operations."""

    default_message = "A movie error occurred."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(self.default_message if message is None else message)


class MovieAlreadyExistsError(BaseMovieError):
    """A movie already has the requested name, year and duration."""

    default_message = (
        "A movie with the same name, release year and duration already exists."
    )


class MovieNotFoundError(BaseMovieError):
    """The requested movie does not exist."""

    default_message = "Movie not found."
