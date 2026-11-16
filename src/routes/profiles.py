import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_s3_storage_client
from database import UserGroupEnum, UserModel, get_db
from exceptions import (
    UserNotActiveError,
    UserNotFoundError,
    UserProfileAlreadyExistsError,
)
from schemas.profiles import ProfileRequestSchema, ProfileResponseSchema
from security.dependencies import get_current_user
from services.profile_crud import create_profile as create_profile_service
from storages import S3StorageInterface

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/users/{user_id}/profile/",
    response_model=ProfileResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_profile(
    user_id: Annotated[int, Path(ge=1)],
    profile_data: ProfileRequestSchema = Depends(ProfileRequestSchema.as_form),
    current_user: UserModel = Depends(get_current_user),
    s3_client: S3StorageInterface = Depends(get_s3_storage_client),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponseSchema:
    current_user_id = current_user.id

    if current_user_id != user_id:
        if current_user.group is None:
            logger.error("User %s has no assigned group", current_user_id)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while checking user permissions.",
            )

        if current_user.group.name != UserGroupEnum.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create this profile.",
            )

    try:
        profile = await create_profile_service(
            db=db,
            user_id=user_id,
            profile_data=profile_data,
            s3_client=s3_client,
        )

        response_data = {
            "id": profile.id,
            "user_id": profile.user_id,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "gender": profile.gender,
            "date_of_birth": profile.date_of_birth,
            "info": profile.info,
            "avatar": (
                await s3_client.get_file_url(file_name=profile.avatar)
                if profile.avatar is not None
                else None
            ),
        }

        return ProfileResponseSchema.model_validate(response_data)

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

    except UserProfileAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "User %s failed to create a profile for user %s",
            current_user_id,
            user_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the profile.",
        ) from error
