from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: UUID
    name: Annotated[str, Field(max_length=250)]
    year: int
    time: int
    imdb: float
    price: Decimal


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieRelatedItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Annotated[str, Field(max_length=100)]


class MovieDetailSchema(MovieListItemSchema):
    votes: int
    meta_score: float | None
    gross: float | None
    description: str

    certification: MovieRelatedItemSchema
    genres: list[MovieRelatedItemSchema]
    stars: list[MovieRelatedItemSchema]
    directors: list[MovieRelatedItemSchema]
