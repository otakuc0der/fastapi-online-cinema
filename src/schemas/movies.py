from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: UUID
    name: str
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
