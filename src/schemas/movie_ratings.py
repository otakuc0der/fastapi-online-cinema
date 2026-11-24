from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class MovieRatingRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: Annotated[int, Field(strict=True, ge=1, le=10)]


class MovieRatingResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movie_id: int
    rating: int


class MovieRatingCurrentResponseSchema(BaseModel):
    movie_id: int
    rating: Annotated[int, Field(ge=1, le=10)] | None


class MovieRatingSummarySchema(BaseModel):
    movie_id: int
    average_rating: Annotated[float, Field(ge=1, le=10)] | None
    ratings_count: Annotated[int, Field(ge=0)]
