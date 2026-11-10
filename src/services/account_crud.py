from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import (
    ActivationTokenModel,
    UserGroupEnum,
    UserGroupModel,
    UserModel,
    accounts_validators,
)
from exceptions import UserAlreadyExistsError, UserGroupNotFoundError


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> UserModel | None:
    return await db.scalar(select(UserModel).where(UserModel.email == email))


async def get_user_group_by_name(
    db: AsyncSession,
    group_name: UserGroupEnum,
) -> UserGroupModel | None:
    return await db.scalar(
        select(UserGroupModel).where(
            UserGroupModel.name == group_name,
        )
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
