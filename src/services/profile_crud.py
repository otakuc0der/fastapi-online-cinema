import logging
from io import BytesIO
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import UserProfileModel
from exceptions import (
    UserNotActiveError,
    UserNotFoundError,
    UserProfileAlreadyExistsError,
    UserProfileNotFoundError,
)
from schemas.profiles import ProfileRequestSchema, ProfileUpdateSchema
from services.account_crud import get_user_by_id_for_update
from storages import S3StorageInterface

logger = logging.getLogger(__name__)


async def get_profile_by_user_id(
    db: AsyncSession,
    user_id: int,
) -> UserProfileModel | None:
    return await db.scalar(
        select(UserProfileModel).where(UserProfileModel.user_id == user_id)
    )


async def upload_profile_avatar(
    user_id: int,
    avatar: UploadFile,
    s3_client: S3StorageInterface,
) -> str:
    avatar_bytes = await avatar.read()

    with Image.open(BytesIO(avatar_bytes), formats=["JPEG", "PNG"]) as image:
        if image.format == "JPEG":
            extension = "jpg"
            content_type = "image/jpeg"
        else:
            extension = "png"
            content_type = "image/png"

    filename = (avatar.filename or "avatar").rsplit(".", 1)[0]
    filename = slugify(filename)[:80] or "avatar"

    avatar_key = f"avatars/{user_id}-{filename}-{uuid4().hex}.{extension}"

    await s3_client.upload_file(
        file_name=avatar_key,
        file_data=avatar_bytes,
        content_type=content_type,
    )

    return avatar_key


async def create_profile(
    db: AsyncSession,
    user_id: int,
    profile_data: ProfileRequestSchema,
    s3_client: S3StorageInterface,
) -> UserProfileModel:
    avatar_key: str | None = None

    try:
        user = await get_user_by_id_for_update(db=db, user_id=user_id)
        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise UserNotActiveError()

        profile = await get_profile_by_user_id(db=db, user_id=user_id)

        if profile is not None:
            raise UserProfileAlreadyExistsError()

        data = profile_data.model_dump(exclude={"avatar"})

        if profile_data.avatar is not None:
            avatar_key = await upload_profile_avatar(
                user_id=user_id,
                avatar=profile_data.avatar,
                s3_client=s3_client,
            )

        profile = UserProfileModel(
            user_id=user_id,
            avatar=avatar_key,
            **data,
        )

        db.add(profile)
        await db.commit()

        return profile

    except Exception:
        await db.rollback()

        if avatar_key is not None:
            try:
                await s3_client.delete_file(file_name=avatar_key)
            except Exception:
                logger.exception(
                    "Failed to delete avatar %s after profile creation failed",
                    avatar_key,
                )

        raise


async def update_profile(
    db: AsyncSession,
    user_id: int,
    profile_data: ProfileUpdateSchema,
) -> UserProfileModel:
    try:
        user = await get_user_by_id_for_update(db=db, user_id=user_id)
        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise UserNotActiveError()

        profile = await get_profile_by_user_id(db=db, user_id=user_id)

        if profile is None:
            raise UserProfileNotFoundError()

        data = profile_data.model_dump(exclude_unset=True)

        for field_name, field_value in data.items():
            setattr(profile, field_name, field_value)

        await db.commit()

        return profile

    except Exception:
        await db.rollback()

        raise


async def update_profile_avatar(
    db: AsyncSession,
    user_id: int,
    avatar: UploadFile,
    s3_client: S3StorageInterface,
) -> UserProfileModel:
    new_avatar_key: str | None = None

    try:
        user = await get_user_by_id_for_update(db=db, user_id=user_id)

        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise UserNotActiveError()

        profile = await get_profile_by_user_id(db=db, user_id=user_id)

        if profile is None:
            raise UserProfileNotFoundError()

        old_avatar_key = profile.avatar

        new_avatar_key = await upload_profile_avatar(
            user_id=user_id,
            avatar=avatar,
            s3_client=s3_client,
        )

        profile.avatar = new_avatar_key

        await db.commit()

    except Exception:
        await db.rollback()

        if new_avatar_key is not None:
            try:
                await s3_client.delete_file(file_name=new_avatar_key)
            except Exception:
                logger.exception(
                    "Failed to delete new avatar %s after profile avatar update failed",
                    new_avatar_key,
                )
        raise

    else:
        if old_avatar_key is not None:
            try:
                await s3_client.delete_file(file_name=old_avatar_key)
            except Exception:
                logger.exception(
                    "Failed to delete old avatar %s after successful profile avatar update",
                    old_avatar_key,
                )

        return profile


async def delete_profile_avatar(
    db: AsyncSession,
    user_id: int,
    s3_client: S3StorageInterface,
) -> UserProfileModel:
    old_avatar_key: str | None = None

    try:
        user = await get_user_by_id_for_update(db=db, user_id=user_id)

        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise UserNotActiveError()

        profile = await get_profile_by_user_id(db=db, user_id=user_id)

        if profile is None:
            raise UserProfileNotFoundError()

        old_avatar_key = profile.avatar
        profile.avatar = None

        await db.commit()

    except Exception:
        await db.rollback()
        raise

    else:
        if old_avatar_key is not None:
            try:
                await s3_client.delete_file(file_name=old_avatar_key)
            except Exception:
                logger.exception(
                    "Failed to delete avatar %s after clearing the profile avatar",
                    old_avatar_key,
                )

        return profile


async def delete_profile(
    db: AsyncSession,
    user_id: int,
    s3_client: S3StorageInterface,
) -> None:
    old_avatar_key: str | None = None

    try:
        user = await get_user_by_id_for_update(db=db, user_id=user_id)

        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise UserNotActiveError()

        profile = await get_profile_by_user_id(db=db, user_id=user_id)

        if profile is None:
            raise UserProfileNotFoundError()

        old_avatar_key = profile.avatar

        await db.delete(profile)
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    else:
        if old_avatar_key is not None:
            try:
                await s3_client.delete_file(file_name=old_avatar_key)
            except Exception:
                logger.exception(
                    "Failed to delete avatar %s after successful profile deletion",
                    old_avatar_key,
                )
