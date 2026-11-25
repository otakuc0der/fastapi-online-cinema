from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class MovieCommentTextBaseSchema(BaseModel):
    text: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=2000,
        ),
    ]


class MovieCommentCreateSchema(MovieCommentTextBaseSchema):
    model_config = ConfigDict(extra="forbid")


class MovieCommentUpdateSchema(MovieCommentTextBaseSchema):
    model_config = ConfigDict(extra="forbid")


class MovieCommentResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    movie_id: int
    text: str
    created_at: datetime
    updated_at: datetime


class MovieCommentListResponseSchema(BaseModel):
    comments: list[MovieCommentResponseSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int
