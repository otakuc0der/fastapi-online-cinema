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
    Response,
    status,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from exceptions import MovieAlreadyExistsError
from schemas import (
    MovieBaseSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)
from schemas.examples.movies import (
    movie_detail_example,
    movie_filtered_list_response_example,
    movie_list_response_example,
    movie_ordered_list_response_example,
    movie_related_filters_response_example,
    movie_updated_detail_example,
)
from services.movie_crud import (
    build_movie_ordering,
    count_movies,
    create_movie_record,
    delete_movie_record,
    get_movie_page,
    get_movie_record,
    update_movie_record,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/movies/",
    name="movie-list",
    operation_id="list_movies",
    response_model=MovieListResponseSchema,
    summary="List movies",
    description=(
        "Browse movies with pagination. Filter by exact release year, inclusive "
        "IMDb bounds, genre, actor, director or certification. Name filters ignore "
        "case and surrounding whitespace. All supplied filters apply together.\n\n"
        "Use **ordering** to sort by **id**, **price**, **year**, **imdb** or "
        "**votes** (vote count). Separate fields with commas; prefix a field "
        "with **-** for descending order. Otherwise, ascending order applies. "
        "Fields are applied in the specified priority order. For example, "
        "**price,-year** sorts by price ascending, then year descending "
        "when prices are equal. Default: **-id**. Descending ID resolves "
        "remaining ties unless ID is explicitly supplied.\n\n"
        "The response includes matching movie and page totals. Navigation links "
        "preserve all filters and ordering and are null when unavailable. "
        "An empty result page returns **404**."
    ),
    response_description="Movie page with matching totals and navigation links.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {
                    "examples": {
                        "catalog": {
                            "summary": "Without filters",
                            "description": (
                                "page=1, per_page=1. Default ordering: -id. "
                                "Illustrative data and totals."
                            ),
                            "value": movie_list_response_example,
                        },
                        "related_filters": {
                            "summary": "Genre, actor, director and certification",
                            "description": (
                                "page=1, per_page=1, genre=Action, "
                                "star=Leonardo DiCaprio, director=Christopher Nolan, "
                                "certification=PG-13. All filters apply together. "
                                "Illustrative data and totals."
                            ),
                            "value": movie_related_filters_response_example,
                        },
                        "filtered_catalog": {
                            "summary": "Year and IMDb range",
                            "description": (
                                "page=1, per_page=1, year=2010, "
                                "imdb_min=8, imdb_max=9. "
                                "Illustrative data and totals."
                            ),
                            "value": movie_filtered_list_response_example,
                        },
                        "ordered_catalog": {
                            "summary": "Price ascending, then year descending",
                            "description": (
                                "page=1, per_page=1, ordering=price,-year. "
                                "Descending ID resolves remaining ties. "
                                "Illustrative data and totals."
                            ),
                            "value": movie_ordered_list_response_example,
                        },
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "No movies on the requested page for the selected filters."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "detail": (
                            "No movies found on this page for the selected filters."
                        ),
                    },
                },
            },
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": (
                "Invalid parameters. Page must be an integer >= 1; per_page "
                "an integer from 1 to 20; year an integer from 1900 to the "
                "current year. IMDb bounds must be from 0 to 10 with "
                "imdb_min <= imdb_max. Name filters must contain non-whitespace "
                "text. Ordering accepts comma-separated fields: id, price, "
                "year, imdb and votes, optionally prefixed with '-'. "
                "Empty items, unsupported fields and repeated fields are rejected."
            ),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "The movie catalog could not be loaded.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": (
                            "Unable to load the movie catalog. "
                            "Please try again later."
                        ),
                    },
                },
            },
        },
    },
)
async def list_movies(
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
    genre: Annotated[
        str | None,
        Query(
            title="Genre name",
            description=(
                "Exact genre name, ignoring case and surrounding whitespace. Optional."
            ),
            examples=["Drama"],
        ),
    ] = None,
    star: Annotated[
        str | None,
        Query(
            title="Actor name",
            description=(
                "Exact actor name, ignoring case and surrounding whitespace. Optional."
            ),
            examples=["Tom Hanks"],
        ),
    ] = None,
    director: Annotated[
        str | None,
        Query(
            title="Director name",
            description=(
                "Exact director name, ignoring case and surrounding whitespace. Optional."
            ),
            examples=["Christopher Nolan"],
        ),
    ] = None,
    certification: Annotated[
        str | None,
        Query(
            title="Certification name",
            description=(
                "Exact certification name, ignoring case and surrounding whitespace. "
                "Optional."
            ),
            examples=["PG-13"],
        ),
    ] = None,
    ordering: Annotated[
        str | None,
        Query(
            title="Movie ordering",
            description=(
                "Comma-separated fields in priority order: id, price, year, imdb, "
                "votes (vote count). Ascending by default; prefix with '-' for "
                "descending. Surrounding whitespace is ignored. Empty items and "
                "repeated fields are rejected. Default: -id. Descending ID is added "
                "as a final tie-breaker unless ID is supplied."
            ),
            examples=["price,-year", "-votes", "-imdb,price"],
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
    """Validate filters and ordering, then return a page with totals and navigation."""
    current_year = datetime.date.today().year

    if year is not None and year > current_year:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Release year cannot be later than the current year ({current_year})."
            ),
        )

    if imdb_min is not None and imdb_max is not None and imdb_min > imdb_max:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "Minimum IMDb rating (imdb_min) cannot be greater than "
                "maximum IMDb rating (imdb_max)."
            ),
        )

    name_filters = {
        "genre": genre,
        "star": star,
        "director": director,
        "certification": certification,
    }

    for field_name, value in name_filters.items():
        if value is not None:
            cleaned_value = value.strip()

            if not cleaned_value:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                        f"Filter '{field_name}' must not be empty "
                        "or contain only whitespace."
                    ),
                )

            name_filters[field_name] = cleaned_value

    genre = name_filters["genre"]
    star = name_filters["star"]
    director = name_filters["director"]
    certification = name_filters["certification"]

    try:
        ordering_expressions = build_movie_ordering(ordering)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    try:
        movies = await get_movie_page(
            db=db,
            page=page,
            per_page=per_page,
            ordering_expressions=ordering_expressions,
            year=year,
            imdb_min=imdb_min,
            imdb_max=imdb_max,
            genre=genre,
            star=star,
            director=director,
            certification=certification,
        )

        if not movies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No movies found on this page for the selected filters.",
            )

        total_items = await count_movies(
            db=db,
            year=year,
            imdb_min=imdb_min,
            imdb_max=imdb_max,
            genre=genre,
            star=star,
            director=director,
            certification=certification,
        )
        total_pages = math.ceil(total_items / per_page)

        router_path = request.url.path

        params_dict: dict[str, int | float | str] = {
            "per_page": per_page,
            "page": page,
        }

        if year is not None:
            params_dict["year"] = year

        if imdb_min is not None:
            params_dict["imdb_min"] = imdb_min

        if imdb_max is not None:
            params_dict["imdb_max"] = imdb_max

        for field_name, value in name_filters.items():
            if value is not None:
                params_dict[field_name] = value

        if ordering is not None:
            params_dict["ordering"] = ordering

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
            movies=[MovieBaseSchema.model_validate(movie) for movie in movies],
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
    name="movie-get",
    operation_id="get_movie",
    response_model=MovieDetailSchema,
    summary="Get movie details",
    description=(
        "Get a movie by ID, including its description, certification, genres, stars "
        "and directors. Missing Metascore and gross revenue are returned as null. "
        "Returns 404 when the movie does not exist."
    ),
    response_description="Full movie details and related entities.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": movie_detail_example,
                },
            },
        },
        404: {
            "description": "No movie exists with this ID.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Movie with ID 1001 was not found.",
                    },
                },
            },
        },
        422: {
            "description": "Movie ID must be an integer greater than or equal to 1.",
        },
        500: {
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
async def get_movie(
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
    try:
        movie = await get_movie_record(db=db, movie_id=movie_id)

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


@router.post(
    "/movies/",
    name="movie-create",
    operation_id="create_movie",
    response_model=MovieDetailSchema,
    summary="Create a movie",
    description=(
        "Create a movie with certification, genres, stars and directors supplied by name. "
        "Exact trimmed name matches are reused; missing related entities are created. "
        "All three relation lists are required but may be empty.\n\n"
        "ID and UUID are generated automatically. Metascore and gross revenue may be "
        "omitted or null. Names and descriptions are trimmed; blank names, duplicate "
        "names within a relation list and unknown fields are rejected. "
        "A duplicate (name, year, time) combination returns 409."
    ),
    response_description="Created movie with generated identifiers and related entities.",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "content": {
                "application/json": {
                    "example": movie_detail_example,
                },
            },
        },
        409: {
            "description": "The name, release year and duration match another movie.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "A movie with the same name, release year and duration already exists.",
                    },
                },
            },
        },
        422: {
            "description": "Invalid or missing fields. Year is from 1900 to the current year; duration is positive, IMDb is 0–10, Metascore is 0–100, and votes, gross and price are non-negative. Price allows eight integer digits and two decimal places. See the request schema for field limits.",
        },
        500: {
            "description": "The movie could not be created or its response could not be loaded.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unable to create the movie. Please try again later.",
                    },
                },
            },
        },
    },
)
async def create_movie(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    try:
        movie = await create_movie_record(db=db, movie_data=movie_data)
        return MovieDetailSchema.model_validate(movie)
    except MovieAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )
    except Exception:
        logger.exception("Failed to create movie '%s'", movie_data.name)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create the movie. Please try again later.",
        )


@router.patch(
    "/movies/{movie_id}/",
    name="movie-update",
    operation_id="update_movie",
    response_model=MovieDetailSchema,
    summary="Update a movie",
    description=(
        "Update only the supplied movie attributes. Omitted fields and related entities "
        "remain unchanged. At least one field is required.\n\n"
        "Only meta_score and gross accept null to clear their values. Other supplied "
        "fields follow the creation limits. ID, UUID and relations cannot be updated "
        "here. Returns 404 for an unknown movie and 409 if the resulting "
        "(name, year, time) combination matches another movie."
    ),
    response_description="Updated movie details, including unchanged relations.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": movie_updated_detail_example,
                },
            },
        },
        404: {
            "description": "No movie exists with this ID.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Movie with ID 1001 was not found.",
                    },
                },
            },
        },
        409: {
            "description": "The name, release year and duration match another movie.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "A movie with the same name, release year and duration already exists.",
                    },
                },
            },
        },
        422: {
            "description": "Invalid ID or update data: empty body, unknown fields, invalid values, or null supplied for a field other than meta_score or gross.",
        },
        500: {
            "description": "The movie could not be updated.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unable to update the movie. Please try again later.",
                    },
                },
            },
        },
    },
)
async def update_movie(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description="Movie ID, greater than or equal to 1.",
            ge=1,
        ),
    ],
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    try:
        movie = await get_movie_record(
            db=db,
            movie_id=movie_id,
        )

        if movie is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie with ID {movie_id} was not found.",
            )

        movie = await update_movie_record(
            db=db,
            movie=movie,
            movie_data=movie_data,
        )

        return MovieDetailSchema.model_validate(movie)

    except HTTPException:
        raise

    except MovieAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )

    except SQLAlchemyError:
        logger.exception("Database error while updating movie %s", movie_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the movie. Please try again later.",
        )

    except Exception:
        logger.exception("Unexpected error while updating movie %s", movie_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the movie. Please try again later.",
        )


@router.delete(
    "/movies/{movie_id}/",
    name="movie-delete",
    operation_id="delete_movie",
    response_class=Response,
    response_model=None,
    summary="Delete a movie",
    description=(
        "Delete a movie and its association rows. Certification, genres, stars and "
        "directors remain available. Returns 204 with no response body, "
        "or 404 when the movie does not exist."
    ),
    response_description="Movie deleted; no response body.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {
            "description": "Movie deleted successfully. The response body is empty.",
        },
        404: {
            "description": "No movie exists with this ID.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Movie with ID 1001 was not found.",
                    },
                },
            },
        },
        422: {
            "description": "Movie ID must be an integer greater than or equal to 1.",
        },
        500: {
            "description": "The movie could not be deleted.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unable to delete the movie. Please try again later.",
                    },
                },
            },
        },
    },
)
async def delete_movie(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description="Movie ID, greater than or equal to 1.",
            ge=1,
        ),
    ],
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        movie = await get_movie_record(db=db, movie_id=movie_id)

        if movie is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie with ID {movie_id} was not found.",
            )

        await delete_movie_record(db=db, movie=movie)

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException:
        raise

    except SQLAlchemyError:
        logger.exception("Database error while deleting movie %s", movie_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete the movie. Please try again later.",
        )

    except Exception:
        logger.exception("Unexpected error while deleting movie %s", movie_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete the movie. Please try again later.",
        )
