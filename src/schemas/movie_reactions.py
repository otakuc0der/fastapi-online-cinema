from pydantic import (
    BaseModel,
    ConfigDict,
    NonNegativeInt,
)

from database import MovieReactionEnum


class MovieReactionRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reaction: MovieReactionEnum


class MovieReactionResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movie_id: int
    reaction: MovieReactionEnum


class MovieReactionSummarySchema(BaseModel):
    movie_id: int
    likes: NonNegativeInt
    dislikes: NonNegativeInt


class MovieReactionCurrentResponseSchema(BaseModel):
    movie_id: int
    reaction: MovieReactionEnum | None
