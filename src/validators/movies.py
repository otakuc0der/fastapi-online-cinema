import datetime


def validate_movie_name(value: object) -> str:
    """Trim a movie title and reject non-string or blank values."""
    if not isinstance(value, str):
        raise ValueError("Value must be a string.")
    name = value.strip()
    if not name:
        raise ValueError("Movie name cannot be empty.")
    return name


def validate_movie_year(value: int) -> int:
    """Reject release years later than the current year."""
    current_year = datetime.date.today().year
    if value > current_year:
        raise ValueError(f"Release year cannot be later than {current_year}.")
    return value


def validate_movie_description(value: str) -> str:
    """Trim a description and reject blank values."""
    description = value.strip()
    if not description:
        raise ValueError("Movie description cannot be empty.")
    return description


def validate_movie_certification(value: object) -> str:
    """Trim a certification name and reject non-string or blank values."""
    if not isinstance(value, str):
        raise ValueError("Value must be a string.")
    certification = value.strip()
    if not certification:
        raise ValueError("Movie certification cannot be empty.")
    return certification


def validate_related_names(values: list[str]) -> list[str]:
    """Trim related names and reject blank, overlong or duplicate entries."""
    cleaned_names: list[str] = []
    seen_names: set[str] = set()
    for value in values:
        name = value.strip()
        if not name:
            raise ValueError("Names must not be empty or contain only whitespace.")
        if len(name) > 100:
            raise ValueError("Each name must be at most 100 characters long.")
        if name in seen_names:
            raise ValueError(f"Duplicate name: '{name}'.")
        seen_names.add(name)
        cleaned_names.append(name)
    return cleaned_names
