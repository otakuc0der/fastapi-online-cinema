import logging
import math
from typing import Annotated
from urllib.parse import urlencode

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import MovieListItemSchema, MovieListResponseSchema
from services.movie_crud import count_movies, fetch_movies_page


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    name="movie-list",
    summary="Get a paginated movie catalog",
    description=(
        "Browse the movie catalog using **page** and **per_page**. "
        "Movies are sorted by ID in descending order.\n\n"
        "The response includes basic movie information, the total number "
        "of movies and pages, and links to the previous and next pages. "
        "A pagination link is `null` when that page does not exist.\n\n"
        "Returns **404** if the catalog is empty or the requested page "
        "contains no movies."
    ),
    response_description="A page of movies with pagination information.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {
                    "example": {
                        "movies": [
                            {
                                "id": 1000,
                                "uuid": "f82e9f31-7d9c-4f87-a403-65498d62c8c7",
                                "name": "Inception",
                                "year": 2010,
                                "time": 148,
                                "imdb": 8.8,
                                "price": "4.99",
                            }
                        ],
                        "prev_page": None,
                        "next_page": "/api/v1/movies/?per_page=1&page=2",
                        "total_pages": 1000,
                        "total_items": 1000,
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The catalog is empty or the requested page has no movies."
            ),
            "content": {
                "application/json": {
                    "example": {"detail": "No movies found."}
                }
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": (
                "Invalid pagination parameters. Page and per_page must be integers. "
                "Page must be at least 1, and per_page must be between 1 and 20."
            ),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "An unexpected error occurred while loading movies.",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to load the movie catalog."}
                }
            },
        },
    },
)
async def movie_list(
    request: Request,
    page: Annotated[
        int,
        Query(
            title="Page number",
            description="Page number starting from 1. Defaults to 1.",
            ge=1,
        ),
    ] = 1,
    per_page: Annotated[
        int,
        Query(
            title="Movies per page",
            description=(
                "Number of movies per page, from 1 to 20. Defaults to 10."
            ),
            ge=1,
            le=20,
        ),
    ] = 10,
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    """Load a movie page and build pagination links."""
    try:
        movies = await fetch_movies_page(db=db, page=page, per_page=per_page)

        if not movies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No movies found.",
            )

        total_items = await count_movies(db=db)
        total_pages = math.ceil(total_items / per_page)

        router_path = request.url.path

        prev_page_link = None
        if page > 1:
            additional_params = urlencode({
                "per_page": per_page,
                "page": page - 1,
            })
            prev_page_link = f"{router_path}?{additional_params}"

        next_page_link = None
        if page < total_pages:
            additional_params = urlencode({
                "per_page": per_page,
                "page": page + 1,
            })
            next_page_link = f"{router_path}?{additional_params}"

        return MovieListResponseSchema(
            movies=[
                MovieListItemSchema.model_validate(movie)
                for movie in movies
            ],
            prev_page=prev_page_link,
            next_page=next_page_link,
            total_pages=total_pages,
            total_items=total_items,
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception("Failed to load the movie catalog")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load the movie catalog.",
        )
