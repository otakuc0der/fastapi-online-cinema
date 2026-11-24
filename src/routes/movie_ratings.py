import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Response,
    status,
)
from fastapi.openapi.models import Example
from sqlalchemy.ext.asyncio import AsyncSession

from database import UserModel, get_db
from exceptions import MovieNotFoundError, UserNotActiveError, UserNotFoundError
from schemas import (
    MovieRatingCurrentResponseSchema,
    MovieRatingRequestSchema,
    MovieRatingResponseSchema,
    MovieRatingSummarySchema,
)
from schemas.examples.movie_ratings import (
    DELETE_MOVIE_RATING_RESPONSES,
    GET_CURRENT_MOVIE_RATING_RESPONSES,
    GET_MOVIE_RATING_SUMMARY_RESPONSES,
    SET_MOVIE_RATING_RESPONSES,
    movie_rating_request_example,
)
from security.dependencies import get_current_user
from services.movie_rating_crud import (
    delete_movie_rating as delete_movie_rating_service,
    get_current_movie_rating as get_current_movie_rating_service,
    get_movie_rating_summary as get_movie_rating_summary_service,
    set_movie_rating as set_movie_rating_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()

MOVIE_RATING_REQUEST_EXAMPLES: dict[str, Example] = {
    "rating": Example(
        summary="Rate the movie",
        value=movie_rating_request_example,
    ),
}


@router.put(
    "/movies/{movie_id}/rating/",
    response_model=MovieRatingResponseSchema,
    summary="Set a movie rating",
    description=(
        "Rate an existing movie with an integer from **1 to 10**. "
        "The user is identified by the Bearer access token. "
        "The request body must contain only the required **rating** field. "
        "Strings, floating-point numbers, booleans and null are rejected.\n\n"
        "Each user can have one rating per movie. If no rating exists, "
        "a new record is created. Otherwise, the existing rating is updated. "
        "Submitting the same rating again is allowed and does not create "
        "duplicates. All successful requests return **200**.\n\n"
        "Other users' ratings remain unchanged. User ratings are independent "
        "of likes, dislikes and the movie's IMDb rating and vote count. "
        "An unknown movie returns **404**.\n\n"
        "Requires a valid Bearer access token for an active user."
    ),
    response_description="Movie ID and the saved user rating.",
    status_code=status.HTTP_200_OK,
    responses=SET_MOVIE_RATING_RESPONSES,
)
async def set_movie_rating(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description="ID of the movie to rate. Must be at least 1.",
            ge=1,
            examples=[17],
        ),
    ],
    rating_data: Annotated[
        MovieRatingRequestSchema,
        Body(openapi_examples=MOVIE_RATING_REQUEST_EXAMPLES),
    ],
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MovieRatingResponseSchema:
    current_user_id = current_user.id

    try:
        rating_record = await set_movie_rating_service(
            db=db,
            user_id=current_user_id,
            movie_id=movie_id,
            rating=rating_data.rating,
        )

        return MovieRatingResponseSchema.model_validate(rating_record)

    except MovieNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except UserNotActiveError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "User %s failed to set a rating for movie %s",
            current_user_id,
            movie_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while setting the movie rating.",
        ) from error


@router.delete(
    "/movies/{movie_id}/rating/",
    response_class=Response,
    summary="Delete your movie rating",
    description=(
        "Delete the authenticated user's rating for an existing movie. "
        "The user is identified by the Bearer access token. "
        "No request body is required.\n\n"
        "Return **204** without a response body. If the user has no rating "
        "for this movie, the request also succeeds. "
        "An unknown movie returns **404**.\n\n"
        "Other users' ratings remain unchanged. The deleted rating "
        "is no longer included in the average or rating count. "
        "Likes, dislikes and IMDb data remain unchanged.\n\n"
        "Requires a valid Bearer access token for an active user."
    ),
    response_description="User rating removed; no response body.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=DELETE_MOVIE_RATING_RESPONSES,
)
async def delete_movie_rating(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description=(
                "ID of the movie whose rating should be removed. " "Must be at least 1."
            ),
            ge=1,
            examples=[17],
        ),
    ],
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    current_user_id = current_user.id

    try:
        await delete_movie_rating_service(
            db=db,
            user_id=current_user_id,
            movie_id=movie_id,
        )

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except MovieNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except UserNotActiveError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "User %s failed to delete a rating for movie %s",
            current_user_id,
            movie_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the movie rating.",
        ) from error


@router.get(
    "/movies/{movie_id}/rating/",
    response_model=MovieRatingCurrentResponseSchema,
    summary="Get your movie rating",
    description=(
        "Return the authenticated user's rating for an existing movie. "
        "The user is identified by the Bearer access token. "
        "Other users' ratings are not returned.\n\n"
        "If the user has not rated the movie, return **200** with "
        "**rating: null**. An unknown movie returns **404**. "
        "This request does not create or modify a rating.\n\n"
        "Requires a valid Bearer access token for an active user."
    ),
    response_description="Movie ID and the current user's rating, or null.",
    status_code=status.HTTP_200_OK,
    responses=GET_CURRENT_MOVIE_RATING_RESPONSES,
)
async def get_current_movie_rating(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description=(
                "ID of the movie whose user rating should be retrieved. "
                "Must be at least 1."
            ),
            ge=1,
            examples=[17],
        ),
    ],
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MovieRatingCurrentResponseSchema:
    current_user_id = current_user.id

    try:
        rating_record = await get_current_movie_rating_service(
            db=db,
            user_id=current_user_id,
            movie_id=movie_id,
        )

        return MovieRatingCurrentResponseSchema(
            movie_id=movie_id,
            rating=(rating_record.rating if rating_record is not None else None),
        )

    except MovieNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "User %s failed to retrieve a rating for movie %s",
            current_user_id,
            movie_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the movie rating.",
        ) from error


@router.get(
    "/movies/{movie_id}/ratings/",
    response_model=MovieRatingSummarySchema,
    summary="Get a movie rating summary",
    description=(
        "Return the arithmetic mean of user ratings and the number "
        "of ratings for an existing movie. Each user contributes "
        "at most one rating, using their latest saved value.\n\n"
        "If the movie has no ratings, return **200** with "
        "**average_rating: null** and **ratings_count: 0**. "
        "The average is returned as a number without explicit rounding "
        "to a fixed number of decimal places. "
        "An unknown movie returns **404**.\n\n"
        "These values describe ratings submitted through this API. "
        "They are independent of likes, dislikes and IMDb data.\n\n"
        "Authentication is not required."
    ),
    response_description="Movie ID, average user rating and rating count.",
    status_code=status.HTTP_200_OK,
    responses=GET_MOVIE_RATING_SUMMARY_RESPONSES,
)
async def get_movie_rating_summary(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description=(
                "ID of the movie whose rating summary should be retrieved. "
                "Must be at least 1."
            ),
            ge=1,
            examples=[17],
        ),
    ],
    db: AsyncSession = Depends(get_db),
) -> MovieRatingSummarySchema:
    try:
        average_rating, ratings_count = await get_movie_rating_summary_service(
            db=db,
            movie_id=movie_id,
        )

        return MovieRatingSummarySchema(
            movie_id=movie_id,
            average_rating=average_rating,
            ratings_count=ratings_count,
        )

    except MovieNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "Failed to retrieve the rating summary for movie %s",
            movie_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the movie rating summary.",
        ) from error
