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
)
from schemas.profiles import ProfileRequestSchema
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
