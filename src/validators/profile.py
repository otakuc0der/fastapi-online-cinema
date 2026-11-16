import re
from datetime import date
from io import BytesIO

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError


def validate_name(name: str) -> None:
    if not re.fullmatch(r"[A-Za-z]+", name):
        raise ValueError("Name must contain only English letters and cannot be empty.")

    if len(name) > 100:
        raise ValueError("Name must not exceed 100 characters.")


def validate_info(info: str) -> None:
    if not info or info.isspace():
        raise ValueError("Info field cannot be empty or contain only spaces.")


def validate_avatar(avatar: UploadFile) -> None:
    max_size = 1024 * 1024
    allowed_formats = "JPEG", "PNG"

    try:
        contents = avatar.file.read(max_size + 1)
        file_size = len(contents)

        if file_size == 0:
            raise ValueError("Avatar file cannot be empty.")

        if file_size > max_size:
            raise ValueError("Avatar size must not exceed 1 MiB.")

        with Image.open(BytesIO(contents), formats=allowed_formats) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as error:
        raise ValueError(
            "Avatar must be a valid, non-corrupted JPEG or PNG image."
        ) from error
    finally:
        avatar.file.seek(0)


def validate_date_of_birth(birth_date: date) -> None:
    if birth_date.year < 1900:
        raise ValueError("Birth year must be 1900 or later.")

    today = date.today()

    if birth_date > today:
        raise ValueError("Date of birth cannot be in the future.")

    age = (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )

    if age < 18:
        raise ValueError("You must be at least 18 years old.")
