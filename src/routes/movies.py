import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Request,
    Response,
    status,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from exceptions import MovieAlreadyExistsError
from routes.dependencies.movies import MovieListParams, get_movie_list_params
from routes.movie_listing import build_movie_page_response
from schemas import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)
from schemas.examples.movies import (
    CREATE_MOVIE_RESPONSES,
    DELETE_MOVIE_RESPONSES,
    GET_MOVIE_RESPONSES,
    LIST_MOVIES_RESPONSES,
    UPDATE_MOVIE_RESPONSES,
)
from security.dependencies import get_current_moderator
from services.movie_crud import (
    create_movie_record,
    delete_movie_record,
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
        "Use **search** for a case-insensitive partial match in the title, "
        "description, actor names or director names. A match in any field is "
        "sufficient. The search text is matched as one phrase; surrounding "
        "whitespace is ignored, and % and _ are literal characters. "
        "Search applies together with all supplied filters.\n\n"
        "Use **ordering** to sort by **id**, **price**, **year**, **imdb** or "
        "**votes** (vote count). Separate fields with commas; prefix a field "
        "with **-** for descending order. Otherwise, ascending order applies. "
        "Fields are applied in priority order. For example, **price,-year** sorts "
        "by price ascending, then year descending when prices are equal. "
        "Default: **-id**. Descending ID resolves remaining ties unless ID "
        "is explicitly supplied.\n\n"
        "The response includes matching movie and page totals. Navigation links "
        "preserve filters, search and ordering and are null when unavailable. "
        "An empty result page returns **404**."
    ),
    response_description="Movie page with matching totals and navigation links.",
    status_code=status.HTTP_200_OK,
    responses=LIST_MOVIES_RESPONSES,
)
async def list_movies(
    request: Request,
    params: Annotated[MovieListParams, Depends(get_movie_list_params)],
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    try:
        return await build_movie_page_response(
            request=request,
            db=db,
            params=params,
            not_found_message="No movies found on this page for the supplied filters and search.",
        )

    except HTTPException:
        raise

    except Exception as error:
        logger.exception("Failed to load the movie catalog")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load the movie catalog. Please try again later.",
        ) from error


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
    responses=GET_MOVIE_RESPONSES,
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
    dependencies=[Depends(get_current_moderator)],
    response_model=MovieDetailSchema,
    summary="Create a movie",
    description=(
        "Create a movie with certification, genres, stars and directors supplied by name. "
        "Related names are trimmed and matched without regard to case. "
        "Existing entities are reused, and missing entities are created. "
        "Genres, stars and directors lists are required but may be empty.\n\n"
        "ID and UUID are generated automatically. Meta_score and gross may be "
        "omitted or null. The movie name and description are trimmed and must not "
        "be blank. Related names must contain 1–100 characters after trimming. "
        "Duplicate names within each relation list are rejected regardless of case. "
        "Unknown request fields are rejected.\n\n"
        "A duplicate (name, year, time) combination returns 409. "
        "Movie names are compared case-sensitively for this check."
        "\n\nRequires a valid Bearer access token for an active moderator "
        "or administrator."
    ),
    response_description="Created movie with generated identifiers and related entities.",
    status_code=status.HTTP_201_CREATED,
    responses=CREATE_MOVIE_RESPONSES,
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
    dependencies=[Depends(get_current_moderator)],
    response_model=MovieDetailSchema,
    summary="Update a movie",
    description=(
        "Update only the supplied movie attributes. Omitted fields and related entities "
        "remain unchanged. At least one field is required.\n\n"
        "Only meta_score and gross accept null to clear their values. Other supplied "
        "fields follow the creation limits. ID, UUID and relations cannot be updated "
        "here. Returns 404 for an unknown movie and 409 if the resulting "
        "(name, year, time) combination matches another movie."
        "\n\nRequires a valid Bearer access token for an active moderator "
        "or administrator."
    ),
    response_description="Updated movie details, including unchanged relations.",
    status_code=status.HTTP_200_OK,
    responses=UPDATE_MOVIE_RESPONSES,
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
    dependencies=[Depends(get_current_moderator)],
    response_class=Response,
    response_model=None,
    summary="Delete a movie",
    description=(
        "Delete a movie and its association rows. Certification, genres, stars and "
        "directors remain available. Returns 204 with no response body, "
        "or 404 when the movie does not exist."
        "\n\nRequires a valid Bearer access token for an active moderator "
        "or administrator."
    ),
    response_description="Movie deleted; no response body.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=DELETE_MOVIE_RESPONSES,
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
