class UserGroupNotFoundError(Exception):
    """A user group with the requested ID does not exist."""

    pass


class UserAlreadyExistsError(Exception):
    """A user already has the requested unique fields."""

    pass
