import logging
import math
from typing import Annotated
from urllib.parse import urlencode

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import (
    MovieDetailSchema,
    MovieListItemSchema,
    MovieListResponseSchema,
)
from schemas.examples.movies import (
    movie_detail_example,
    movie_list_response_example,
)
from services.movie_crud import count_movies, fetch_movies_page, get_movie_record_by_id

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
    response_description="A page of movies with pagination totals and navigation links.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {"example": movie_list_response_example},
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The catalog is empty or the requested page has no movies.",
            "content": {
                "application/json": {"example": {"detail": "No movies found."}},
            },
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": (
                "Invalid pagination parameters. Page and per_page must be integers. "
                "Page must be at least 1, and per_page must be between 1 and 20."
            ),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "An unexpected error occurred while loading the movie catalog.",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to load the movie catalog."},
                },
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
            description="Number of movies per page, from 1 to 20. Defaults to 10.",
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

        params_dict = {
            "per_page": per_page,
            "page": page,
        }

        prev_page_link = None
        if page > 1:
            params_dict["page"] = page - 1
            additional_params = urlencode(params_dict)
            prev_page_link = f"{router_path}?{additional_params}"

        next_page_link = None
        if page < total_pages:
            params_dict["page"] = page + 1
            additional_params = urlencode(params_dict)
            next_page_link = f"{router_path}?{additional_params}"

        return MovieListResponseSchema(
            movies=[MovieListItemSchema.model_validate(movie) for movie in movies],
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


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    name="movie-detail",
    summary="Get movie details",
    description=(
        "Retrieve a movie by its ID. The response includes movie attributes, "
        "certification, genres, stars and directors.\n\n"
        "Returns **404** if a movie with the given ID does not exist."
    ),
    response_description="Detailed movie information with related entities.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {"example": movie_detail_example},
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "A movie with the given ID was not found.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Movie with the given ID (1001) was not found.",
                    },
                },
            },
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Movie ID must be an integer greater than or equal to 1.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "An unexpected error occurred while loading movie details.",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to load movie details."},
                },
            },
        },
    },
)
async def get_movie_by_id(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description="ID of the movie to retrieve. Must be at least 1.",
            ge=1,
        ),
    ],
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    """Load a movie with its certification, genres, stars and directors."""
    try:
        movie = await get_movie_record_by_id(db=db, movie_id=movie_id)

        if movie is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie with the given ID ({movie_id}) was not found.",
            )

        return MovieDetailSchema.model_validate(movie)

    except HTTPException:
        raise

    except Exception:
        logger.exception("Failed to load details for movie ID %s", movie_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load movie details.",
        )
