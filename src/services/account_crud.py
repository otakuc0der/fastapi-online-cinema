from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import (
    ActivationTokenModel,
    UserGroupEnum,
    UserGroupModel,
    UserModel,
    accounts_validators,
)
from database.models.accounts import TokenBaseModel
from exceptions import UserAlreadyExistsError, UserGroupNotFoundError


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> UserModel | None:
    return await db.scalar(select(UserModel).where(UserModel.email == email))


async def get_user_by_email_for_update(
    db: AsyncSession,
    email: str,
) -> UserModel | None:
    return await db.scalar(
        select(UserModel)
        .where(UserModel.email == email)
        .with_for_update(of=UserModel)
        .execution_options(populate_existing=True)
    )


async def get_user_group_by_name(
    db: AsyncSession,
    group_name: UserGroupEnum,
) -> UserGroupModel | None:
    return await db.scalar(
        select(UserGroupModel).where(
            UserGroupModel.name == group_name,
        )
    )


def get_token_expires_at(
    token_record: TokenBaseModel,
) -> datetime:
    token_expires_at = token_record.expires_at

    if token_expires_at.tzinfo is None:
        token_expires_at = token_expires_at.replace(
            tzinfo=timezone.utc,
        )

    return token_expires_at


async def get_activation_token(
    db: AsyncSession,
    email: str,
    token: str,
) -> ActivationTokenModel | None:
    return await db.scalar(
        select(ActivationTokenModel)
        .join(ActivationTokenModel.user)
        .options(joinedload(ActivationTokenModel.user))
        .where(
            UserModel.email == email,
            ActivationTokenModel.token == token,
        )
        .with_for_update(of=ActivationTokenModel)
    )


async def get_activation_token_by_user_id(
    db: AsyncSession,
    user_id: int,
) -> ActivationTokenModel | None:
    return await db.scalar(
        select(ActivationTokenModel)
        .where(ActivationTokenModel.user_id == user_id)
        .with_for_update(of=ActivationTokenModel)
    )


async def register_user(
    db: AsyncSession,
    email: str,
    raw_password: str,
) -> tuple[UserModel, ActivationTokenModel]:
    try:
        email = accounts_validators.validate_email(email)

        user = await get_user_by_email(db=db, email=email)

        if user is not None:
            raise UserAlreadyExistsError(
                f"A user with this email {email} already exists."
            )

        group = await get_user_group_by_name(
            db=db,
            group_name=UserGroupEnum.USER,
        )

        if group is None:
            raise UserGroupNotFoundError("Default user group was not found.")

        new_user = UserModel.create(
            email=email,
            raw_password=raw_password,
            group_id=group.id,
        )

        db.add(new_user)
        await db.flush()

        activation_token = ActivationTokenModel(
            user_id=new_user.id,
        )
        db.add(activation_token)

        await db.commit()

        return new_user, activation_token

    except IntegrityError as error:
        await db.rollback()

        constraint_name = getattr(
            error.orig.__cause__,
            "constraint_name",
            None,
        )

        if constraint_name == "ix_users_email":
            raise UserAlreadyExistsError(
                f"A user with this email {email} already exists."
            ) from error

        raise

    except Exception:
        await db.rollback()
        raise
