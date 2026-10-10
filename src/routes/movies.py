import datetime
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
    movie_filtered_list_response_example,
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
        "List movies by descending ID with pagination. "
        "Filter by exact release year and an inclusive IMDb rating range. "
        "All provided filters apply together.\n\n"
        "Returns matching movie and page totals. Navigation links preserve filters "
        "and are `null` when unavailable. Returns **404** for an empty result page."
    ),
    response_description="Movies, pagination totals and navigation links.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {
                    "examples": {
                        "catalog": {
                            "summary": "Without filters",
                            "description": (
                                "page=1, per_page=1. Illustrative data and totals."
                            ),
                            "value": movie_list_response_example,
                        },
                        "filtered_catalog": {
                            "summary": "Release year and IMDb range",
                            "description": (
                                "page=1, per_page=1, year=2010, "
                                "imdb_min=8, imdb_max=9. Illustrative data and totals."
                            ),
                            "value": movie_filtered_list_response_example,
                        },
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "No movies on the requested page for the selected filters.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No movies found on this page for the selected filters.",
                    },
                },
            },
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": (
                "Invalid parameters: integer page >= 1, integer per_page from 1 to 20, "
                "integer year from 1900 to the current year, "
                "and IMDb bounds from 0 to 10 with imdb_min <= imdb_max."
            ),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "The movie catalog could not be loaded.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unable to load the movie catalog. Please try again later.",
                    },
                },
            },
        },
    },
)
async def movie_list(
    request: Request,
    year: Annotated[
        int | None,
        Query(
            title="Release year",
            description="Exact release year, from 1900 to the current year. Optional.",
            ge=1900,
        ),
    ] = None,
    imdb_min: Annotated[
        float | None,
        Query(
            title="Minimum IMDb rating",
            description=(
                "Inclusive minimum, from 0 to 10. Optional. "
                "Must be <= imdb_max when both are provided."
            ),
            ge=0,
            le=10,
        ),
    ] = None,
    imdb_max: Annotated[
        float | None,
        Query(
            title="Maximum IMDb rating",
            description=(
                "Inclusive maximum, from 0 to 10. Optional. "
                "Must be >= imdb_min when both are provided."
            ),
            ge=0,
            le=10,
        ),
    ] = None,
    page: Annotated[
        int,
        Query(
            title="Page number",
            description="Page number, starting from 1. Default: 1.",
            ge=1,
        ),
    ] = 1,
    per_page: Annotated[
        int,
        Query(
            title="Movies per page",
            description="Movies per page, from 1 to 20. Default: 10.",
            ge=1,
            le=20,
        ),
    ] = 10,
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    """Validate filters and return a movie page with navigation links."""
    current_year = datetime.date.today().year

    if year is not None and year > current_year:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Release year cannot be later than the current year ({current_year}).",
        )

    if imdb_min is not None and imdb_max is not None and imdb_min > imdb_max:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Minimum IMDb rating (imdb_min) cannot be greater than maximum IMDb rating (imdb_max).",
        )

    try:
        movies = await fetch_movies_page(
            db=db,
            page=page,
            per_page=per_page,
            year=year,
            imdb_min=imdb_min,
            imdb_max=imdb_max,
        )

        if not movies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No movies found on this page for the selected filters.",
            )

        total_items = await count_movies(
            db=db, year=year, imdb_min=imdb_min, imdb_max=imdb_max
        )
        total_pages = math.ceil(total_items / per_page)

        router_path = request.url.path

        params_dict: dict[str, int | float] = {
            "per_page": per_page,
            "page": page,
        }

        if year is not None:
            params_dict["year"] = year

        if imdb_min is not None:
            params_dict["imdb_min"] = imdb_min

        if imdb_max is not None:
            params_dict["imdb_max"] = imdb_max

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
            detail="Unable to load the movie catalog. Please try again later.",
        )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    name="movie-detail",
    summary="Get movie details",
    description=(
        "Get a movie by ID with its certification, genres, stars and directors. "
        "Returns **404** if the movie does not exist."
    ),
    response_description="Movie details and related entities.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {"example": movie_detail_example},
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "No movie exists with the requested ID.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with ID 1001 was not found."},
                },
            },
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Movie ID must be an integer greater than or equal to 1.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Movie details could not be loaded.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unable to load movie details. Please try again later.",
                    },
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
            description="Movie ID, greater than or equal to 1.",
            ge=1,
        ),
    ],
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    """Return a movie with its related entities."""
    try:
        movie = await get_movie_record_by_id(db=db, movie_id=movie_id)

        if movie is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie with ID {movie_id} was not found.",
            )

        return MovieDetailSchema.model_validate(movie)

    except HTTPException:
        raise

    except Exception:
        logger.exception("Failed to load details for movie ID %s", movie_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load movie details. Please try again later.",
        )
