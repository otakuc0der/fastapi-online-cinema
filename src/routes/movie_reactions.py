import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import UserModel, get_db
from exceptions import MovieNotFoundError, UserNotActiveError, UserNotFoundError
from schemas.movie_reactions import (
    MovieReactionCurrentResponseSchema,
    MovieReactionRequestSchema,
    MovieReactionResponseSchema,
    MovieReactionSummarySchema,
)
from schemas.examples.movie_reactions import (
    DELETE_MOVIE_REACTION_RESPONSES,
    GET_CURRENT_MOVIE_REACTION_RESPONSES,
    GET_MOVIE_REACTION_SUMMARY_RESPONSES,
    MOVIE_REACTION_REQUEST_EXAMPLES,
    SET_MOVIE_REACTION_RESPONSES,
)
from security.dependencies import get_current_user
from services.movie_crud import get_movie_record
from services.movie_reaction_crud import (
    count_movie_reactions,
    delete_movie_reaction as delete_movie_reaction_service,
    get_movie_reaction,
    set_movie_reaction as set_movie_reaction_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.put(
    "/movies/{movie_id}/reaction/",
    response_model=MovieReactionResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Set a movie reaction",
    description=(
        "Set the authenticated user's reaction to a movie. A valid Bearer access "
        "token for an active account is required, any user group is allowed. "
        "Send an application/json body with reaction set to 'like' or 'dislike'. "
        "The user is identified by the access token, do not supply user_id.\n\n"
        "Each user has at most one reaction per movie. The first request creates "
        "a reaction, another value updates the existing record. Repeating the "
        "same value leaves that reaction in place without creating duplicates. "
        "Both creation and updates return 200. Use DELETE on this path to remove "
        "a reaction, null is not accepted by PUT."
    ),
    response_description="The current user's saved movie reaction.",
    responses=SET_MOVIE_REACTION_RESPONSES,
)
async def set_movie_reaction(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description="ID of the movie. Must be at least 1.",
            ge=1,
            examples=[17],
        ),
    ],
    reaction_data: Annotated[
        MovieReactionRequestSchema,
        Body(openapi_examples=MOVIE_REACTION_REQUEST_EXAMPLES),
    ],
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MovieReactionResponseSchema:
    current_user_id = current_user.id

    try:
        reaction_record = await set_movie_reaction_service(
            db=db,
            user_id=current_user_id,
            movie_id=movie_id,
            reaction=reaction_data.reaction,
        )

        return MovieReactionResponseSchema.model_validate(reaction_record)

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
            "User %s failed to set a reaction for movie %s",
            current_user_id,
            movie_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while setting the movie reaction.",
        ) from error


@router.delete(
    "/movies/{movie_id}/reaction/",
    response_class=Response,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove my movie reaction",
    description=(
        "Remove the authenticated user's like or dislike for an existing movie. "
        "A valid Bearer access token for an active account is required. "
        "No request body or user_id is needed. Other users' reactions are not "
        "modified.\n\n"
        "Return 204 without a response body whether the reaction was removed "
        "or already absent. Repeated deletion succeeds. An unknown movie "
        "returns 404 even when the user has no reaction."
    ),
    response_description="The reaction is absent, no response body.",
    responses=DELETE_MOVIE_REACTION_RESPONSES,
)
async def delete_movie_reaction(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description="ID of the movie. Must be at least 1.",
            ge=1,
            examples=[17],
        ),
    ],
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    current_user_id = current_user.id

    try:
        await delete_movie_reaction_service(
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
            "User %s failed to delete a reaction for movie %s",
            current_user_id,
            movie_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the movie reaction.",
        ) from error


@router.get(
    "/movies/{movie_id}/reactions/",
    response_model=MovieReactionSummarySchema,
    status_code=status.HTTP_200_OK,
    summary="Get movie reaction counts",
    description=(
        "Return the total numbers of likes and dislikes for an existing movie. "
        "This endpoint is public and does not require authentication. The "
        "response contains aggregate counts, not user identities.\n\n"
        "An existing movie with no reactions returns 200 with likes and dislikes "
        "both set to zero. An unknown movie returns 404. These counts describe "
        "user reactions in this application and are separate from IMDb votes "
        "and ratings."
    ),
    response_description="Movie ID and the total numbers of likes and dislikes.",
    responses=GET_MOVIE_REACTION_SUMMARY_RESPONSES,
)
async def get_movie_reaction_summary(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description="ID of the movie. Must be at least 1.",
            ge=1,
            examples=[17],
        ),
    ],
    db: AsyncSession = Depends(get_db),
) -> MovieReactionSummarySchema:
    try:
        movie = await get_movie_record(db=db, movie_id=movie_id)

        if movie is None:
            raise MovieNotFoundError()

        likes, dislikes = await count_movie_reactions(
            db=db,
            movie_id=movie_id,
        )

        return MovieReactionSummarySchema(
            movie_id=movie_id,
            likes=likes,
            dislikes=dislikes,
        )

    except MovieNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "Failed to count reactions for movie %s",
            movie_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving movie reactions.",
        ) from error


@router.get(
    "/movies/{movie_id}/reaction/",
    response_model=MovieReactionCurrentResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get my movie reaction",
    description=(
        "Return the authenticated user's current reaction to an existing movie. "
        "A valid Bearer access token for an active account is required, any user "
        "group is allowed. The user is identified by the access token.\n\n"
        "Return 200 with reaction set to 'like', 'dislike' or null when the user "
        "has not reacted or has removed the reaction. Other users' reactions "
        "are not returned. An unknown movie returns 404. For public totals, "
        "use GET /movies/{movie_id}/reactions/ instead."
    ),
    response_description="Movie ID and the current user's reaction, or null.",
    responses=GET_CURRENT_MOVIE_REACTION_RESPONSES,
)
async def get_current_movie_reaction(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description="ID of the movie. Must be at least 1.",
            ge=1,
            examples=[17],
        ),
    ],
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MovieReactionCurrentResponseSchema:
    current_user_id = current_user.id

    try:
        movie = await get_movie_record(db=db, movie_id=movie_id)

        if movie is None:
            raise MovieNotFoundError()

        reaction_record = await get_movie_reaction(
            db=db,
            user_id=current_user_id,
            movie_id=movie_id,
        )

        return MovieReactionCurrentResponseSchema(
            movie_id=movie_id,
            reaction=(
                reaction_record.reaction if reaction_record is not None else None
            ),
        )

    except MovieNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "User %s failed to retrieve a reaction for movie %s",
            current_user_id,
            movie_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the movie reaction.",
        ) from error
