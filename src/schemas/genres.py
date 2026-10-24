from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    field_validator,
)

from schemas.examples.genres import (
    genre_create_example,
    genre_list_item_example,
    genre_schema_example,
    genre_update_example,
)
from validators.reference_entities import validate_reference_name


class GenreSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [genre_schema_example]},
    )

    id: int
    name: Annotated[str, Field(min_length=1, max_length=100)]


class GenreListItemSchema(GenreSchema):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [genre_list_item_example]},
    )

    movie_count: NonNegativeInt


class GenreCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [genre_create_example]},
    )

    name: Annotated[str, Field(min_length=1, max_length=100)]

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: object) -> str:
        return validate_reference_name(value)


class GenreUpdateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [genre_update_example]},
    )

    name: Annotated[str, Field(min_length=1, max_length=100)]

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: object) -> str:
        return validate_reference_name(value)
