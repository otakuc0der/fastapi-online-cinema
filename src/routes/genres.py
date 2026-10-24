import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from exceptions import GenreAlreadyExistsError
from schemas import (
    GenreCreateSchema,
    GenreListItemSchema,
    GenreSchema,
    GenreUpdateSchema,
)
from schemas.examples.genres import (
    genre_list_response_example,
    genre_updated_response_example,
)
from services.genre_crud import (
    create_genre_record,
    delete_genre_record,
    get_genre_list,
    get_genre_record,
    update_genre_record,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/genres/",
    name="genre-list",
    operation_id="list_genres",
    response_model=list[GenreListItemSchema],
    summary="List genres with movie counts",
    description=(
        "Return all genres ordered by name. "
        "Each genre includes the number of associated movies; "
        "genres without movies have a count of zero.\n\n"
        "Use a genre filter on the movie catalog to browse related movies. "
        "An empty genre collection returns an empty list."
    ),
    response_description="Genre list with movie counts.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": genre_list_response_example,
                },
            },
        },
        500: {
            "description": "The genre list could not be loaded.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": (
                            "Unable to load the genre list. " "Please try again later."
                        ),
                    },
                },
            },
        },
    },
)
async def list_genres(
    db: AsyncSession = Depends(get_db),
) -> list[GenreListItemSchema]:
    try:
        genres = await get_genre_list(db=db)

        return [
            GenreListItemSchema(
                id=genre.id,
                name=genre.name,
                movie_count=movie_count,
            )
            for genre, movie_count in genres
        ]

    except Exception:
        logger.exception("Failed to load the genre list")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load the genre list. Please try again later.",
        )


@router.get(
    "/genres/{genre_id}/",
    name="genre-detail",
    operation_id="get_genre",
    response_model=GenreSchema,
    summary="Get genre details",
    description=(
        "Return a genre's ID and name. "
        "Associated movies are available through the movie catalog filters. "
        "Return 404 if the genre does not exist."
    ),
    response_description="Genre ID and name.",
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "The genre does not exist.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Genre with ID 9999 was not found.",
                    },
                },
            },
        },
        422: {
            "description": "Genre ID must be an integer greater than zero.",
        },
        500: {
            "description": "Genre details could not be loaded.",
        },
    },
)
async def get_genre(
    genre_id: Annotated[
        int,
        Path(
            title="Genre ID",
            description="ID of the genre to retrieve. Must be at least 1.",
            ge=1,
        ),
    ],
    db: AsyncSession = Depends(get_db),
) -> GenreSchema:
    try:
        genre = await get_genre_record(db=db, genre_id=genre_id)

        if genre is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Genre with ID {genre_id} was not found.",
            )

        return GenreSchema.model_validate(genre)

    except HTTPException:
        raise

    except Exception:
        logger.exception("Failed to load genre %s", genre_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load the genre. Please try again later.",
        )


@router.post(
    "/genres/",
    name="genre-create",
    operation_id="create_genre",
    response_model=GenreSchema,
    summary="Create a genre",
    description=(
        "Create a genre using a unique name. "
        "Leading and trailing whitespace is removed. "
        "The cleaned name must contain 1–100 characters.\n\n"
        "Names are checked for duplicates without regard to case. "
        "Unknown request fields are rejected. "
        "Creating a genre does not associate it with movies."
    ),
    response_description="Created genre with its generated ID.",
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            "description": "A genre with the same name already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "A genre with the same name already exists.",
                    },
                },
            },
        },
        422: {
            "description": (
                "Name is missing, is not a string, is blank after trimming, "
                "or exceeds 100 characters; or unknown fields were supplied."
            ),
        },
        500: {
            "description": "The genre could not be created.",
        },
    },
)
async def create_genre(
    genre_data: GenreCreateSchema,
    db: AsyncSession = Depends(get_db),
) -> GenreSchema:
    try:
        genre = await create_genre_record(
            db=db,
            genre_data=genre_data,
        )

        return GenreSchema.model_validate(genre)

    except GenreAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A genre with the same name already exists.",
        )

    except Exception:
        logger.exception(
            "Failed to create genre '%s'",
            genre_data.name,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create the genre. Please try again later.",
        )


@router.patch(
    "/genres/{genre_id}/",
    name="genre-update",
    operation_id="update_genre",
    response_model=GenreSchema,
    summary="Rename a genre",
    description=(
        "Update a genre's name while preserving its ID and movie associations. "
        "The name field is required; an empty request body is rejected.\n\n"
        "Leading and trailing whitespace is removed. "
        "The cleaned name must contain 1–100 characters. "
        "Names are checked for duplicates without regard to case, "
        "excluding the current record. "
        "Submitting the current name is allowed. Unknown fields are rejected."
    ),
    response_description="Genre with the updated name.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": genre_updated_response_example,
                },
            },
        },
        404: {
            "description": "The genre does not exist.",
        },
        409: {
            "description": "Another genre already has the requested name.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "A genre with the same name already exists.",
                    },
                },
            },
        },
        422: {
            "description": (
                "Invalid genre ID or name. Name is required and must contain "
                "1–100 characters after trimming. Unknown fields are rejected."
            ),
        },
        500: {
            "description": "The genre could not be updated.",
        },
    },
)
async def update_genre(
    genre_id: Annotated[
        int,
        Path(
            title="Genre ID",
            description="ID of the genre to rename. Must be at least 1.",
            ge=1,
        ),
    ],
    genre_data: GenreUpdateSchema,
    db: AsyncSession = Depends(get_db),
) -> GenreSchema:
    try:
        genre = await get_genre_record(db=db, genre_id=genre_id)

        if genre is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Genre with ID {genre_id} was not found.",
            )

        genre = await update_genre_record(
            db=db,
            genre=genre,
            genre_data=genre_data,
        )

        return GenreSchema.model_validate(genre)

    except HTTPException:
        raise

    except GenreAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A genre with the same name already exists.",
        )

    except Exception:
        logger.exception("Failed to update genre %s", genre_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the genre. Please try again later.",
        )


@router.delete(
    "/genres/{genre_id}/",
    name="genre-delete",
    operation_id="delete_genre",
    response_model=None,
    summary="Delete a genre",
    description=(
        "Delete a genre and its movie associations. "
        "Associated movies remain in the catalog. "
        "Return 204 without a response body, or 404 if the genre does not exist."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {
            "description": "Genre deleted. No response body.",
        },
        404: {
            "description": "The genre does not exist.",
        },
        422: {
            "description": "Genre ID must be an integer greater than zero.",
        },
        500: {
            "description": "The genre could not be deleted.",
        },
    },
)
async def delete_genre(
    genre_id: Annotated[
        int,
        Path(
            title="Genre ID",
            description="ID of the genre to delete. Must be at least 1.",
            ge=1,
        ),
    ],
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        genre = await get_genre_record(db=db, genre_id=genre_id)

        if genre is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Genre with ID {genre_id} was not found.",
            )

        await delete_genre_record(db=db, genre=genre)

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException:
        raise

    except Exception:
        logger.exception("Failed to delete genre %s", genre_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete the genre. Please try again later.",
        )
