import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Response, status
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
from schemas.examples.profiles import (
    CREATE_PROFILE_RESPONSES,
    DELETE_AVATAR_RESPONSES,
    DELETE_PROFILE_RESPONSES,
    GET_PROFILE_RESPONSES,
    PROFILE_UPDATE_EXAMPLES,
    UPDATE_AVATAR_RESPONSES,
    UPDATE_PROFILE_RESPONSES,
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
    summary="Get a user profile",
    description=(
        "Retrieve a profile belonging to the authenticated user or another user "
        "if the caller is an administrator. The response contains a public "
        "avatar URL or null. Constructing the URL does not contact S3 storage."
    ),
    responses=GET_PROFILE_RESPONSES,
)
async def get_profile(
    user_id: Annotated[
        int,
        Path(ge=1, description="ID of the user who owns the profile.", examples=[17]),
    ],
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
    summary="Create a user profile",
    description=(
        "Create one profile for an active user. Access is restricted to the "
        "profile owner and administrators. Send fields using "
        "multipart/form-data: first_name, last_name, gender, date_of_birth and "
        "info are required. Avatar is optional. Names must contain only English "
        "letters, be at most 100 characters and are stored in lowercase. The "
        "biography must not be blank. Birth year must be 1900 or later, the "
        "user must be at least 18 years old. Avatars must be valid JPEG or PNG "
        "images up to 1 MiB (1,048,576 bytes). Avatar keys are stored in the "
        "database, responses contain public URLs. If database saving fails "
        "after upload, the service attempts to remove the new object."
    ),
    responses=CREATE_PROFILE_RESPONSES,
)
async def create_profile(
    user_id: Annotated[
        int,
        Path(ge=1, description="ID of the user who owns the profile.", examples=[17]),
    ],
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
    summary="Partially update a user profile",
    description=(
        "Update profile fields using application/json. Access is restricted to "
        "the profile owner and administrators. Only supplied fields change, "
        "explicit null values and unknown fields are rejected. An empty object "
        "is accepted and leaves the profile unchanged. Names, biography and "
        "birth date follow the same validation rules as profile creation. Use "
        "the separate avatar endpoints to upload, replace or remove an avatar."
    ),
    responses=UPDATE_PROFILE_RESPONSES,
)
async def update_profile(
    user_id: Annotated[
        int,
        Path(ge=1, description="ID of the user who owns the profile.", examples=[17]),
    ],
    profile_data: Annotated[
        ProfileUpdateSchema,
        Body(
            description=(
                "Fields to update. Omitted fields remain unchanged. "
                "Explicit null values and unknown fields are rejected. "
                "An empty object is allowed. Avatar updates use the separate avatar endpoint."
            ),
            openapi_examples=PROFILE_UPDATE_EXAMPLES,
        ),
    ],
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
    summary="Upload or replace a profile avatar",
    description=(
        "Upload a required avatar file using multipart/form-data. Access is "
        "restricted to the profile owner and administrators. The image must be "
        "a non-empty valid JPEG or PNG file up to 1 MiB (1,048,576 bytes). The "
        "new object is uploaded before its key is saved. If database saving "
        "fails, removal of the new object is attempted. After a successful "
        "save, removal of the previous object is attempted. Failure to remove "
        "the old object is logged, the updated profile is still returned, and "
        "no automatic retry is scheduled."
    ),
    responses=UPDATE_AVATAR_RESPONSES,
)
async def update_avatar(
    user_id: Annotated[
        int,
        Path(ge=1, description="ID of the user who owns the profile.", examples=[17]),
    ],
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
    summary="Remove a profile avatar",
    description=(
        "Clear the avatar reference while keeping the profile and user account. "
        "Access is restricted to the profile owner and administrators. If the "
        "profile already has no avatar, the operation still succeeds and "
        "returns avatar: null. Avatar storage cleanup is attempted after the "
        "database change is committed. A cleanup failure is logged and does not "
        "change the successful response. There is no automatic retry, an "
        "unremoved public object may remain accessible by its old URL."
    ),
    responses=DELETE_AVATAR_RESPONSES,
)
async def delete_avatar(
    user_id: Annotated[
        int,
        Path(ge=1, description="ID of the user who owns the profile.", examples=[17]),
    ],
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
    summary="Delete a user profile",
    description=(
        "Delete the profile while preserving the user account, credentials and "
        "group membership. Access is restricted to the profile owner and "
        "administrators. Return 204 without a response body. Repeated deletion "
        "returns 404 because the profile no longer exists. Avatar storage "
        "cleanup is attempted after the database change is committed. A cleanup "
        "failure is logged and does not change the successful response. There "
        "is no automatic retry, an unremoved public object may remain "
        "accessible by its old URL."
    ),
    responses=DELETE_PROFILE_RESPONSES,
)
async def delete_profile(
    user_id: Annotated[
        int,
        Path(ge=1, description="ID of the user who owns the profile.", examples=[17]),
    ],
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
