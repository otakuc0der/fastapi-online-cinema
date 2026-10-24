from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    field_validator,
)

from schemas.examples.stars import (
    star_create_example,
    star_list_response_example,
    star_schema_example,
    star_update_example,
)
from validators.reference_entities import validate_reference_name


class StarSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [star_schema_example]},
    )

    id: int
    name: Annotated[str, Field(min_length=1, max_length=100)]


class StarCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [star_create_example]},
    )

    name: Annotated[str, Field(min_length=1, max_length=100)]

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: object) -> str:
        return validate_reference_name(value)


class StarUpdateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [star_update_example]},
    )

    name: Annotated[str, Field(min_length=1, max_length=100)]

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: object) -> str:
        return validate_reference_name(value)


class StarListResponseSchema(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [star_list_response_example]},
    )

    stars: list[StarSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: NonNegativeInt
    total_items: NonNegativeInt
