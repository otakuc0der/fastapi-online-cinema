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
from sqlalchemy.ext.asyncio import AsyncSession

from database import UserModel, get_db
from exceptions import MovieNotFoundError, UserNotActiveError, UserNotFoundError
from routes.dependencies.movies import MovieListParams, get_movie_list_params
from routes.movie_listing import build_movie_page_response
from schemas import MovieFavoriteResponseSchema, MovieListResponseSchema
from schemas.examples.movie_favorites import (
    ADD_MOVIE_TO_FAVORITES_RESPONSES,
    LIST_FAVORITE_MOVIES_RESPONSES,
    REMOVE_MOVIE_FROM_FAVORITES_RESPONSES,
)
from security.dependencies import get_current_user
from services.movie_favorite_crud import (
    add_movie_to_favorites as add_movie_to_favorites_service,
    remove_movie_from_favorites as remove_movie_from_favorites_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/movies/favorites/",
    response_model=MovieListResponseSchema,
    summary="List favorite movies",
    description=(
        "Browse the authenticated user's favorite movies with pagination. "
        "The user is identified by the Bearer access token. "
        "Other users' favorites are not included.\n\n"
        "Filter by exact release year, inclusive IMDb bounds, genre ID, "
        "genre name, actor, director or certification. Name filters match "
        "exactly without regard to case or surrounding whitespace. "
        "All supplied filters apply together. If genre and genre_id are "
        "both supplied, both conditions must match, possibly through "
        "different genres of the same movie.\n\n"
        "Use **search** for a case-insensitive partial match in the title, "
        "description, actor names or director names. A match in any field "
        "is sufficient. Search text is matched as one phrase, surrounding "
        "whitespace is ignored, and % and _ are literal characters. "
        "Search applies together with the supplied filters.\n\n"
        "Use **ordering** to sort by **id**, **price**, **year**, **imdb** "
        "or **votes** (IMDb vote count). Separate fields with commas and "
        "prefix a field with **-** for descending order. Otherwise, "
        "ascending order applies. Fields are applied in priority order. "
        "For example, **price,-year** sorts by price ascending and then "
        "year descending. Default: **-id**. Descending ID resolves remaining "
        "ties unless ID is explicitly supplied. Empty items, unsupported "
        "fields and repeated fields are rejected.\n\n"
        "The response includes matching movie and page totals. Navigation "
        "links preserve filters, search and ordering and are null when "
        "unavailable. An empty favorites list, no matching movies or "
        "an empty result page returns **404**.\n\n"
        "Requires a valid Bearer access token for an active user."
    ),
    response_description=(
        "Favorite movie page with matching totals and navigation links."
    ),
    status_code=status.HTTP_200_OK,
    responses=LIST_FAVORITE_MOVIES_RESPONSES,
)
async def list_favorite_movies(
    request: Request,
    params: Annotated[MovieListParams, Depends(get_movie_list_params)],
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    current_user_id = current_user.id

    try:
        return await build_movie_page_response(
            request=request,
            db=db,
            params=params,
            not_found_message=(
                "No favorite movies found on this page "
                "for the supplied filters and search."
            ),
            favorite_user_id=current_user_id,
        )

    except HTTPException:
        raise

    except Exception as error:
        logger.exception(
            "User %s failed to load favorite movies",
            current_user_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load favorite movies. Please try again later.",
        ) from error


@router.put(
    "/movies/{movie_id}/favorite/",
    response_model=MovieFavoriteResponseSchema,
    summary="Add a movie to favorites",
    description=(
        "Add an existing movie to the authenticated user's favorites. "
        "The user is identified by the Bearer access token. "
        "No request body is required.\n\n"
        "First and repeated requests return **200** with the user and movie "
        "IDs. Repeated requests do not create duplicate records and do not "
        "remove the movie from favorites. Other users' favorites remain "
        "unchanged. An unknown movie returns **404**.\n\n"
        "Requires a valid Bearer access token for an active user."
    ),
    response_description="Identifiers of the user and favorite movie.",
    status_code=status.HTTP_200_OK,
    responses=ADD_MOVIE_TO_FAVORITES_RESPONSES,
)
async def add_movie_to_favorites(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description="ID of the movie. Must be at least 1.",
            ge=1,
            examples=[1000],
        ),
    ],
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MovieFavoriteResponseSchema:
    current_user_id = current_user.id

    try:
        await add_movie_to_favorites_service(
            db=db,
            user_id=current_user_id,
            movie_id=movie_id,
        )

        return MovieFavoriteResponseSchema(
            user_id=current_user_id,
            movie_id=movie_id,
        )

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
            "User %s failed to add movie %s to favorites",
            current_user_id,
            movie_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while adding the movie to favorites.",
        ) from error


@router.delete(
    "/movies/{movie_id}/favorite/",
    response_class=Response,
    summary="Remove a movie from favorites",
    description=(
        "Remove an existing movie from the authenticated user's favorites. "
        "The user is identified by the Bearer access token. "
        "No request body is required.\n\n"
        "Return **204** without a response body. If the movie is already "
        "absent from the user's favorites, the request also succeeds. "
        "The movie itself and other users' favorites remain unchanged. "
        "An unknown movie returns **404**.\n\n"
        "Requires a valid Bearer access token for an active user."
    ),
    response_description="Movie removed from favorites, no response body.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=REMOVE_MOVIE_FROM_FAVORITES_RESPONSES,
)
async def remove_movie_from_favorites(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description="ID of the movie. Must be at least 1.",
            ge=1,
            examples=[1000],
        ),
    ],
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    current_user_id = current_user.id

    try:
        await remove_movie_from_favorites_service(
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
            "User %s failed to remove movie %s from favorites",
            current_user_id,
            movie_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while removing the movie from favorites.",
        ) from error
