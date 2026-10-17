from decimal import Decimal
from typing import Annotated, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveInt,
    field_validator,
    model_validator,
)

from schemas.examples.movies import (
    certification_schema_example,
    director_schema_example,
    movie_create_example,
    movie_detail_example,
    movie_list_item_example,
    movie_list_response_example,
    movie_update_example,
)
from schemas.genres import GenreSchema
from schemas.stars import StarSchema
from validators.movies import (
    validate_movie_certification,
    validate_movie_description,
    validate_movie_name,
    validate_movie_year,
    validate_related_names,
)


class MovieBaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [movie_list_item_example]},
    )

    id: int
    uuid: UUID
    name: Annotated[str, Field(max_length=250)]
    year: int
    time: int
    imdb: float
    price: Decimal = Field(
        description="Price serialized as a decimal string.", examples=["4.99"]
    )


class MovieListResponseSchema(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [movie_list_response_example]}
    )

    movies: list[MovieBaseSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class CertificationSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [certification_schema_example]},
    )
    id: int
    name: Annotated[str, Field(max_length=100)]


class DirectorSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [director_schema_example]},
    )
    id: int
    name: Annotated[str, Field(max_length=100)]


class MovieDetailSchema(MovieBaseSchema):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [movie_detail_example]},
    )
    votes: int
    meta_score: float | None
    gross: float | None
    description: str
    certification: CertificationSchema
    genres: list[GenreSchema]
    stars: list[StarSchema]
    directors: list[DirectorSchema]


class MovieCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        json_schema_extra={"examples": [movie_create_example]},
    )
    name: Annotated[str, Field(min_length=1, max_length=250)]
    year: Annotated[
        int, Field(ge=1900, description="Release year up to the current year.")
    ]
    time: PositiveInt = Field(description="Duration in minutes.")
    imdb: Annotated[float, Field(ge=0, le=10)]
    price: Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]
    votes: NonNegativeInt
    meta_score: Annotated[float, Field(ge=0, le=100)] | None = None
    gross: NonNegativeFloat | None = None
    description: str
    certification: Annotated[str, Field(min_length=1, max_length=100)]
    genres: list[str]
    stars: list[str]
    directors: list[str]

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: object) -> str:
        return validate_movie_name(value)

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int) -> int:
        return validate_movie_year(value)

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        return validate_movie_description(value)

    @field_validator("certification", mode="before")
    @classmethod
    def validate_certification(cls, value: object) -> str:
        return validate_movie_certification(value)

    @field_validator("genres", "stars", "directors")
    @classmethod
    def validate_names(cls, values: list[str]) -> list[str]:
        return validate_related_names(values)


class MovieUpdateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        json_schema_extra={"examples": [movie_update_example]},
    )
    name: Annotated[str, Field(min_length=1, max_length=250)] = None
    year: Annotated[int, Field(ge=1900)] = None
    time: PositiveInt = None
    imdb: Annotated[float, Field(ge=0, le=10)] = None
    price: Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)] = None
    votes: NonNegativeInt = None
    meta_score: Annotated[float, Field(ge=0, le=100)] | None = None
    gross: NonNegativeFloat | None = None
    description: str = None

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: object) -> str:
        return validate_movie_name(value)

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int) -> int:
        return validate_movie_year(value)

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        return validate_movie_description(value)

    @model_validator(mode="after")
    def validate_update_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update.")
        return self
