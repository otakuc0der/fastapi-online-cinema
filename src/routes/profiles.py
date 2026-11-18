import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_s3_storage_client
from database import (
    UserGroupEnum,
    UserModel,
    UserProfileModel,
    get_db,
)
from exceptions import (
    UserNotActiveError,
    UserNotFoundError,
    UserProfileAlreadyExistsError,
    UserProfileNotFoundError,
)
from schemas import (
    ProfileAvatarUpdateSchema,
    ProfileRequestSchema,
    ProfileResponseSchema,
    ProfileUpdateSchema,
)
from security.dependencies import get_current_user
from services.profile_crud import (
    create_profile as create_profile_service,
    delete_profile as delete_profile_service,
    delete_profile_avatar,
    get_profile_by_user_id,
    update_profile as update_profile_service,
    update_profile_avatar,
)
from storages import S3StorageInterface

logger = logging.getLogger(__name__)

router = APIRouter()


def check_profile_permissions(
    current_user: UserModel,
    user_id: int,
) -> None:
    if current_user.id != user_id:
        if current_user.group is None:
            logger.error("User %s has no assigned group", current_user.id)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while checking user permissions.",
            )

        if current_user.group.name != UserGroupEnum.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this profile.",
            )


async def build_profile_response(
    profile: UserProfileModel,
    s3_client: S3StorageInterface,
) -> ProfileResponseSchema:
    avatar_url = (
        await s3_client.get_file_url(file_name=profile.avatar)
        if profile.avatar is not None
        else None
    )

    return ProfileResponseSchema(
        id=profile.id,
        user_id=profile.user_id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        gender=profile.gender,
        date_of_birth=profile.date_of_birth,
        info=profile.info,
        avatar=avatar_url,
    )


@router.get(
    "/users/{user_id}/profile/",
    response_model=ProfileResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_profile(
    user_id: Annotated[int, Path(ge=1)],
    current_user: UserModel = Depends(get_current_user),
    s3_client: S3StorageInterface = Depends(get_s3_storage_client),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponseSchema:
    current_user_id = current_user.id

    check_profile_permissions(
        current_user=current_user,
        user_id=user_id,
    )

    try:
        profile = await get_profile_by_user_id(db=db, user_id=user_id)

        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found.",
            )

        return await build_profile_response(
            profile=profile,
            s3_client=s3_client,
        )

    except HTTPException:
        raise

    except Exception as error:
        logger.exception(
            "User %s failed to retrieve a profile for user %s",
            current_user_id,
            user_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the profile.",
        ) from error


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

    check_profile_permissions(
        current_user=current_user,
        user_id=user_id,
    )

    try:
        profile = await create_profile_service(
            db=db,
            user_id=user_id,
            profile_data=profile_data,
            s3_client=s3_client,
        )

        return await build_profile_response(
            profile=profile,
            s3_client=s3_client,
        )

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


@router.patch(
    "/users/{user_id}/profile/",
    response_model=ProfileResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_profile(
    user_id: Annotated[int, Path(ge=1)],
    profile_data: ProfileUpdateSchema,
    current_user: UserModel = Depends(get_current_user),
    s3_client: S3StorageInterface = Depends(get_s3_storage_client),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponseSchema:
    current_user_id = current_user.id

    check_profile_permissions(
        current_user=current_user,
        user_id=user_id,
    )

    try:
        profile = await update_profile_service(
            db=db,
            user_id=user_id,
            profile_data=profile_data,
        )

        return await build_profile_response(
            profile=profile,
            s3_client=s3_client,
        )

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

    except UserProfileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "User %s failed to update a profile for user %s",
            current_user_id,
            user_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the profile.",
        ) from error


@router.put(
    "/users/{user_id}/profile/avatar/",
    response_model=ProfileResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_avatar(
    user_id: Annotated[int, Path(ge=1)],
    avatar_data: ProfileAvatarUpdateSchema = Depends(
        ProfileAvatarUpdateSchema.as_form,
    ),
    current_user: UserModel = Depends(get_current_user),
    s3_client: S3StorageInterface = Depends(get_s3_storage_client),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponseSchema:
    current_user_id = current_user.id

    check_profile_permissions(
        current_user=current_user,
        user_id=user_id,
    )

    try:
        profile = await update_profile_avatar(
            db=db,
            user_id=user_id,
            avatar=avatar_data.avatar,
            s3_client=s3_client,
        )

        return await build_profile_response(
            profile=profile,
            s3_client=s3_client,
        )

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

    except UserProfileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "User %s failed to update the avatar for user %s",
            current_user_id,
            user_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the profile avatar.",
        ) from error


@router.delete(
    "/users/{user_id}/profile/avatar/",
    response_model=ProfileResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def delete_avatar(
    user_id: Annotated[int, Path(ge=1)],
    current_user: UserModel = Depends(get_current_user),
    s3_client: S3StorageInterface = Depends(get_s3_storage_client),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponseSchema:
    current_user_id = current_user.id

    check_profile_permissions(
        current_user=current_user,
        user_id=user_id,
    )

    try:
        profile = await delete_profile_avatar(
            db=db,
            user_id=user_id,
            s3_client=s3_client,
        )

        return await build_profile_response(
            profile=profile,
            s3_client=s3_client,
        )

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

    except UserProfileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "User %s failed to delete the avatar for user %s",
            current_user_id,
            user_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the profile avatar.",
        ) from error


@router.delete(
    "/users/{user_id}/profile/",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_profile(
    user_id: Annotated[int, Path(ge=1)],
    current_user: UserModel = Depends(get_current_user),
    s3_client: S3StorageInterface = Depends(get_s3_storage_client),
    db: AsyncSession = Depends(get_db),
) -> Response:
    current_user_id = current_user.id

    check_profile_permissions(
        current_user=current_user,
        user_id=user_id,
    )

    try:
        await delete_profile_service(
            db=db,
            user_id=user_id,
            s3_client=s3_client,
        )

        return Response(status_code=status.HTTP_204_NO_CONTENT)

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

    except UserProfileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "User %s failed to delete the profile for user %s",
            current_user_id,
            user_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the profile.",
        ) from error
