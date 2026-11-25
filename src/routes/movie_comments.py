import logging
import math
from typing import Annotated

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database import UserModel, get_db
from exceptions import (
    MovieCommentNotFoundError,
    MovieCommentPermissionError,
    MovieNotFoundError,
    UserNotActiveError,
    UserNotFoundError,
)
from routes.utils import build_pagination_links
from schemas import (
    MovieCommentCreateSchema,
    MovieCommentListResponseSchema,
    MovieCommentResponseSchema,
    MovieCommentUpdateSchema,
)
from schemas.examples.movie_comments import (
    CREATE_MOVIE_COMMENT_RESPONSES,
    DELETE_MOVIE_COMMENT_RESPONSES,
    GET_MOVIE_COMMENT_RESPONSES,
    LIST_MOVIE_COMMENTS_RESPONSES,
    MOVIE_COMMENT_CREATE_REQUEST_EXAMPLES,
    MOVIE_COMMENT_UPDATE_REQUEST_EXAMPLES,
    UPDATE_MOVIE_COMMENT_RESPONSES,
)
from security.dependencies import get_current_user
from services.movie_comment_crud import (
    count_movie_comments,
    create_movie_comment as create_movie_comment_service,
    delete_movie_comment as delete_movie_comment_service,
    get_movie_comment as get_movie_comment_service,
    get_movie_comment_page,
    update_movie_comment as update_movie_comment_service,
)
from services.movie_crud import get_movie_record

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/movies/{movie_id}/comments/",
    response_model=MovieCommentListResponseSchema,
    summary="List movie comments",
    description=(
        "Browse comments for an existing movie with pagination. "
        "Authentication is not required.\n\n"
        "Comments are ordered by creation time descending, then by ID "
        "descending to resolve ties. New comments appear first. "
        "Editing a comment does not change its position in this ordering.\n\n"
        "The response includes comment and page totals. Relative navigation "
        "links preserve the page size and are null when unavailable.\n\n"
        "If the movie has no comments, the first page returns **200** with "
        "an empty list, zero totals and null navigation links. "
        "An empty page with a number greater than 1 returns **404**. "
        "An unknown movie also returns **404**."
    ),
    response_description=("Comment page with totals and relative navigation links."),
    status_code=status.HTTP_200_OK,
    responses=LIST_MOVIE_COMMENTS_RESPONSES,
)
async def list_movie_comments(
    request: Request,
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description="ID of the movie. Must be at least 1.",
            ge=1,
            examples=[1000],
        ),
    ],
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
            title="Comments per page",
            description="Comments per page, from 1 to 20. Default: 10.",
            ge=1,
            le=20,
        ),
    ] = 10,
    db: AsyncSession = Depends(get_db),
) -> MovieCommentListResponseSchema:
    try:
        movie = await get_movie_record(db=db, movie_id=movie_id)

        if movie is None:
            raise MovieNotFoundError()

        comments = await get_movie_comment_page(
            db=db,
            movie_id=movie_id,
            page=page,
            per_page=per_page,
        )

        if not comments and page > 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No comments found on the requested page.",
            )

        total_items = await count_movie_comments(
            db=db,
            movie_id=movie_id,
        )
        total_pages = math.ceil(total_items / per_page)

        prev_page_link, next_page_link = build_pagination_links(
            path=request.url.path,
            page=page,
            total_pages=total_pages,
            query_params={
                "page": page,
                "per_page": per_page,
            },
        )

        return MovieCommentListResponseSchema(
            comments=[
                MovieCommentResponseSchema.model_validate(comment)
                for comment in comments
            ],
            prev_page=prev_page_link,
            next_page=next_page_link,
            total_pages=total_pages,
            total_items=total_items,
        )

    except HTTPException:
        raise

    except MovieNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "Failed to load comments for movie %s",
            movie_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving movie comments.",
        ) from error


@router.get(
    "/movies/{movie_id}/comments/{comment_id}/",
    response_model=MovieCommentResponseSchema,
    summary="Get a movie comment",
    description=(
        "Get a comment by its ID within the specified movie. "
        "Authentication is not required.\n\n"
        "The response contains the comment text, author ID, movie ID, "
        "creation time and last update time.\n\n"
        "Returns **404** if the movie or comment does not exist, "
        "or the comment belongs to another movie."
    ),
    response_description="Comment text, author ID, movie ID and timestamps.",
    status_code=status.HTTP_200_OK,
    responses=GET_MOVIE_COMMENT_RESPONSES,
)
async def get_movie_comment(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description="ID of the movie. Must be at least 1.",
            ge=1,
            examples=[1000],
        ),
    ],
    comment_id: Annotated[
        int,
        Path(
            title="Comment ID",
            description=(
                "ID of a comment belonging to the specified movie. "
                "Must be at least 1."
            ),
            ge=1,
            examples=[42],
        ),
    ],
    db: AsyncSession = Depends(get_db),
) -> MovieCommentResponseSchema:
    try:
        movie = await get_movie_record(db=db, movie_id=movie_id)

        if movie is None:
            raise MovieNotFoundError()

        comment_record = await get_movie_comment_service(
            db=db,
            movie_id=movie_id,
            comment_id=comment_id,
        )

        if comment_record is None:
            raise MovieCommentNotFoundError()

        return MovieCommentResponseSchema.model_validate(comment_record)

    except (MovieNotFoundError, MovieCommentNotFoundError) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "Failed to retrieve comment %s for movie %s",
            comment_id,
            movie_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the movie comment.",
        ) from error


@router.post(
    "/movies/{movie_id}/comments/",
    response_model=MovieCommentResponseSchema,
    summary="Create a movie comment",
    description=(
        "Create a comment for an existing movie. The author is identified "
        "by the Bearer access token.\n\n"
        "The request body must contain **text** with 1–2000 characters "
        "after trimming surrounding whitespace. Missing text, null, "
        "blank text and additional request fields are rejected. "
        "Author ID, movie ID, comment ID and timestamps cannot be "
        "supplied in the request body.\n\n"
        "Each successful request creates a separate comment. "
        "A user may leave multiple comments on the same movie, "
        "including comments with identical text.\n\n"
        "Returns **201** with the generated ID and timestamps. "
        "An unknown movie returns **404**.\n\n"
        "Requires a valid Bearer access token for an active user."
    ),
    response_description="Created comment with generated ID and timestamps.",
    status_code=status.HTTP_201_CREATED,
    responses=CREATE_MOVIE_COMMENT_RESPONSES,
)
async def create_movie_comment(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description="ID of the movie to comment on. Must be at least 1.",
            ge=1,
            examples=[1000],
        ),
    ],
    comment_data: Annotated[
        MovieCommentCreateSchema,
        Body(
            description=(
                "Comment text. Surrounding whitespace is removed, "
                "1–2000 characters must remain."
            ),
            openapi_examples=MOVIE_COMMENT_CREATE_REQUEST_EXAMPLES,
        ),
    ],
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MovieCommentResponseSchema:
    current_user_id = current_user.id

    try:
        comment_record = await create_movie_comment_service(
            db=db,
            user_id=current_user_id,
            movie_id=movie_id,
            comment_data=comment_data,
        )

        return MovieCommentResponseSchema.model_validate(comment_record)

    except (MovieNotFoundError, UserNotFoundError) as error:
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
            "User %s failed to create a comment for movie %s",
            current_user_id,
            movie_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the movie comment.",
        ) from error


@router.patch(
    "/movies/{movie_id}/comments/{comment_id}/",
    response_model=MovieCommentResponseSchema,
    summary="Update a movie comment",
    description=(
        "Replace the text of a comment belonging to the authenticated user. "
        "Only the author can edit the comment. Moderators and administrators "
        "cannot edit other users' comments.\n\n"
        "The request body must contain **text** with 1–2000 characters "
        "after trimming surrounding whitespace. Missing text, null, "
        "blank text and additional request fields are rejected.\n\n"
        "Changing the text updates **updated_at**. The comment ID, author, "
        "movie and creation time remain unchanged. Sending the current "
        "text is allowed.\n\n"
        "Returns **404** if the movie or comment does not exist, "
        "or the comment belongs to another movie. Attempting to edit "
        "another user's comment returns **403**.\n\n"
        "Requires a valid Bearer access token for an active user."
    ),
    response_description="Comment with its updated text and timestamps.",
    status_code=status.HTTP_200_OK,
    responses=UPDATE_MOVIE_COMMENT_RESPONSES,
)
async def update_movie_comment(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description="ID of the movie. Must be at least 1.",
            ge=1,
            examples=[1000],
        ),
    ],
    comment_id: Annotated[
        int,
        Path(
            title="Comment ID",
            description=(
                "ID of the authenticated user's comment within the "
                "specified movie. Must be at least 1."
            ),
            ge=1,
            examples=[42],
        ),
    ],
    comment_data: Annotated[
        MovieCommentUpdateSchema,
        Body(
            description=(
                "Replacement comment text. Surrounding whitespace is "
                "removed, 1–2000 characters must remain."
            ),
            openapi_examples=MOVIE_COMMENT_UPDATE_REQUEST_EXAMPLES,
        ),
    ],
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MovieCommentResponseSchema:
    current_user_id = current_user.id

    try:
        comment_record = await update_movie_comment_service(
            db=db,
            user_id=current_user_id,
            movie_id=movie_id,
            comment_id=comment_id,
            comment_data=comment_data,
        )

        return MovieCommentResponseSchema.model_validate(comment_record)

    except (
        MovieNotFoundError,
        MovieCommentNotFoundError,
        UserNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except (UserNotActiveError, MovieCommentPermissionError) as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "User %s failed to update comment %s for movie %s",
            current_user_id,
            comment_id,
            movie_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the movie comment.",
        ) from error


@router.delete(
    "/movies/{movie_id}/comments/{comment_id}/",
    response_class=Response,
    response_model=None,
    summary="Delete a movie comment",
    description=(
        "Delete a comment from the specified movie. No request body "
        "is required.\n\n"
        "The comment author may delete their own comment. Administrators "
        "may also delete other users' comments. Moderators may delete "
        "only their own comments.\n\n"
        "Returns **204** without a response body. The movie and its other "
        "comments remain unchanged.\n\n"
        "Returns **404** if the movie or comment does not exist, "
        "or the comment belongs to another movie. Repeating a successful "
        "deletion also returns **404**. A user who is neither the author "
        "nor an administrator receives **403**.\n\n"
        "Requires a valid Bearer access token for an active user."
    ),
    response_description="Comment deleted, no response body.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=DELETE_MOVIE_COMMENT_RESPONSES,
)
async def delete_movie_comment(
    movie_id: Annotated[
        int,
        Path(
            title="Movie ID",
            description="ID of the movie. Must be at least 1.",
            ge=1,
            examples=[1000],
        ),
    ],
    comment_id: Annotated[
        int,
        Path(
            title="Comment ID",
            description=(
                "ID of the comment to delete within the specified movie. "
                "Must be at least 1."
            ),
            ge=1,
            examples=[42],
        ),
    ],
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    current_user_id = current_user.id

    try:
        await delete_movie_comment_service(
            db=db,
            user_id=current_user_id,
            movie_id=movie_id,
            comment_id=comment_id,
        )

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except (
        MovieNotFoundError,
        MovieCommentNotFoundError,
        UserNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except (UserNotActiveError, MovieCommentPermissionError) as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "User %s failed to delete comment %s for movie %s",
            current_user_id,
            comment_id,
            movie_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the movie comment.",
        ) from error
