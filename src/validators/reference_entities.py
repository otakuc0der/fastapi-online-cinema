def validate_reference_name(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Name must be a string.")

    name = value.strip()

    if not name:
        raise ValueError("Name must not be empty or contain only whitespace.")

    return name
