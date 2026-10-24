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
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from exceptions import StarAlreadyExistsError
from schemas import (
    StarCreateSchema,
    StarListResponseSchema,
    StarSchema,
    StarUpdateSchema,
)
from schemas.examples.stars import star_updated_response_example
from services.star_crud import (
    count_star_records,
    create_star_record,
    delete_star_record,
    get_star_list,
    get_star_record,
    update_star_record,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/stars/",
    name="star-list",
    operation_id="list_stars",
    response_model=StarListResponseSchema,
    summary="List actors",
    description=(
        "Browse actor records, represented as stars, ordered by name. "
        "Use page and per_page to navigate the collection.\n\n"
        "The response includes totals and relative navigation links. "
        "Unavailable links are null. "
        "An empty collection or a page without actors returns 404."
    ),
    response_description="Actor page with totals and navigation links.",
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "No actors exist on the requested page.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No stars found on the requested page.",
                    },
                },
            },
        },
        422: {
            "description": (
                "Page must be an integer greater than zero. "
                "Per_page must be an integer from 1 to 20."
            ),
        },
        500: {
            "description": "The actor list could not be loaded.",
        },
    },
)
async def list_stars(
    request: Request,
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
            title="Actors per page",
            description="Actors per page, from 1 to 20. Default: 10.",
            ge=1,
            le=20,
        ),
    ] = 10,
    db: AsyncSession = Depends(get_db),
) -> StarListResponseSchema:
    try:
        stars = await get_star_list(
            db=db,
            page=page,
            per_page=per_page,
        )

        if not stars:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No stars found on the requested page.",
            )

        total_items = await count_star_records(db=db)
        total_pages = math.ceil(total_items / per_page)

        router_path = request.url.path
        params_dict = {
            "per_page": per_page,
            "page": page,
        }

        prev_page_link = None
        if page > 1:
            params_dict["page"] = page - 1
            prev_page_link = f"{router_path}?{urlencode(params_dict)}"

        next_page_link = None
        if page < total_pages:
            params_dict["page"] = page + 1
            next_page_link = f"{router_path}?{urlencode(params_dict)}"

        return StarListResponseSchema(
            stars=[StarSchema.model_validate(star) for star in stars],
            prev_page=prev_page_link,
            next_page=next_page_link,
            total_pages=total_pages,
            total_items=total_items,
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception("Failed to load the star list")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load the star list. Please try again later.",
        )


@router.get(
    "/stars/{star_id}/",
    name="star-detail",
    operation_id="get_star",
    response_model=StarSchema,
    summary="Get actor details",
    description=(
        "Return an actor's ID and name. "
        "Associated movies are available through the star filter "
        "on the movie catalog. Return 404 if the actor does not exist."
    ),
    response_description="Actor ID and name.",
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "The actor does not exist.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Star with ID 9999 was not found.",
                    },
                },
            },
        },
        422: {
            "description": "Star ID must be an integer greater than zero.",
        },
        500: {
            "description": "Actor details could not be loaded.",
        },
    },
)
async def get_star(
    star_id: Annotated[
        int,
        Path(
            title="Star ID",
            description="ID of the actor to retrieve. Must be at least 1.",
            ge=1,
        ),
    ],
    db: AsyncSession = Depends(get_db),
) -> StarSchema:
    try:
        star = await get_star_record(db=db, star_id=star_id)

        if star is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Star with ID {star_id} was not found.",
            )

        return StarSchema.model_validate(star)

    except HTTPException:
        raise

    except Exception:
        logger.exception("Failed to load star %s", star_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load the star. Please try again later.",
        )


@router.post(
    "/stars/",
    name="star-create",
    operation_id="create_star",
    response_model=StarSchema,
    summary="Create an actor",
    description=(
        "Create an actor record. Leading and trailing whitespace is removed. "
        "The cleaned name must contain 1–100 characters.\n\n"
        "Names are checked for duplicates without regard to case. "
        "Unknown request fields are rejected. "
        "Creating an actor does not associate the record with movies."
    ),
    response_description="Created actor with its generated ID.",
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            "description": "An actor record with the same name already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "A star with the same name already exists.",
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
            "description": "The actor could not be created.",
        },
    },
)
async def create_star(
    star_data: StarCreateSchema,
    db: AsyncSession = Depends(get_db),
) -> StarSchema:
    try:
        star = await create_star_record(
            db=db,
            star_data=star_data,
        )

        return StarSchema.model_validate(star)

    except StarAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A star with the same name already exists.",
        )

    except Exception:
        logger.exception(
            "Failed to create star '%s'",
            star_data.name,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create the star. Please try again later.",
        )


@router.patch(
    "/stars/{star_id}/",
    name="star-update",
    operation_id="update_star",
    response_model=StarSchema,
    summary="Rename an actor",
    description=(
        "Update an actor's name while preserving the ID and movie associations. "
        "The name field is required, an empty request body is rejected.\n\n"
        "Leading and trailing whitespace is removed. "
        "The cleaned name must contain 1–100 characters. "
        "Names are checked for duplicates without regard to case, "
        "excluding the current record. Keeping the current name or changing "
        "only its letter case is allowed. Unknown fields are rejected."
    ),
    response_description="Actor with the updated name.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": star_updated_response_example,
                },
            },
        },
        404: {
            "description": "The actor does not exist.",
        },
        409: {
            "description": "Another actor record already has the requested name.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "A star with the same name already exists.",
                    },
                },
            },
        },
        422: {
            "description": (
                "Invalid star ID or name. Name is required and must contain "
                "1–100 characters after trimming. Unknown fields are rejected."
            ),
        },
        500: {
            "description": "The actor could not be updated.",
        },
    },
)
async def update_star(
    star_id: Annotated[
        int,
        Path(
            title="Star ID",
            description="ID of the actor to rename. Must be at least 1.",
            ge=1,
        ),
    ],
    star_data: StarUpdateSchema,
    db: AsyncSession = Depends(get_db),
) -> StarSchema:
    try:
        star = await get_star_record(db=db, star_id=star_id)

        if star is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Star with ID {star_id} was not found.",
            )

        star = await update_star_record(
            db=db,
            star=star,
            star_data=star_data,
        )

        return StarSchema.model_validate(star)

    except HTTPException:
        raise

    except StarAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A star with the same name already exists.",
        )

    except Exception:
        logger.exception("Failed to update star %s", star_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the star. Please try again later.",
        )


@router.delete(
    "/stars/{star_id}/",
    name="star-delete",
    operation_id="delete_star",
    response_model=None,
    summary="Delete an actor",
    description=(
        "Delete an actor record and its movie associations. "
        "Associated movies remain in the catalog. "
        "Return 204 without a response body, or 404 if the actor does not exist."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {
            "description": "Actor deleted. No response body.",
        },
        404: {
            "description": "The actor does not exist.",
        },
        422: {
            "description": "Star ID must be an integer greater than zero.",
        },
        500: {
            "description": "The actor could not be deleted.",
        },
    },
)
async def delete_star(
    star_id: Annotated[
        int,
        Path(
            title="Star ID",
            description="ID of the actor to delete. Must be at least 1.",
            ge=1,
        ),
    ],
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        star = await get_star_record(db=db, star_id=star_id)

        if star is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Star with ID {star_id} was not found.",
            )

        await delete_star_record(db=db, star=star)

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException:
        raise

    except Exception:
        logger.exception("Failed to delete star %s", star_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete the star. Please try again later.",
        )
