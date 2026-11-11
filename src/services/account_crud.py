from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import (
    ActivationTokenModel,
    PasswordResetTokenModel,
    RefreshTokenModel,
    UserGroupEnum,
    UserGroupModel,
    UserModel,
    accounts_validators,
)
from database.models.accounts import TokenBaseModel
from exceptions import (
    InvalidActivationTokenError,
    InvalidCredentialsError,
    InvalidPasswordError,
    InvalidPasswordResetTokenError,
    InvalidTokenError,
    PasswordUnchangedError,
    TokenExpiredError,
    UserAlreadyActiveError,
    UserAlreadyExistsError,
    UserGroupNotFoundError,
    UserNotActiveError,
    UserNotFoundError,
)
from security.interfaces import JWTAuthManagerInterface
from services.utils import generate_secure_token


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


async def get_user_by_id(
    db: AsyncSession,
    user_id: int,
) -> UserModel | None:
    return await db.scalar(
        select(UserModel)
        .options(joinedload(UserModel.group))
        .where(UserModel.id == user_id)
    )


async def get_user_by_id_for_update(
    db: AsyncSession,
    user_id: int,
) -> UserModel | None:
    return await db.scalar(
        select(UserModel)
        .where(UserModel.id == user_id)
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


async def get_refresh_token(
    db: AsyncSession,
    token: str,
) -> RefreshTokenModel | None:
    return await db.scalar(
        select(RefreshTokenModel)
        .options(joinedload(RefreshTokenModel.user))
        .where(RefreshTokenModel.token == token)
    )


async def get_password_reset_token_by_user_id(
    db: AsyncSession,
    user_id: int,
) -> PasswordResetTokenModel | None:
    return await db.scalar(
        select(PasswordResetTokenModel)
        .where(PasswordResetTokenModel.user_id == user_id)
        .with_for_update(of=PasswordResetTokenModel)
    )


async def get_password_reset_token(
    db: AsyncSession,
    email: str,
    token: str,
) -> PasswordResetTokenModel | None:
    return await db.scalar(
        select(PasswordResetTokenModel)
        .join(PasswordResetTokenModel.user)
        .options(joinedload(PasswordResetTokenModel.user))
        .where(
            UserModel.email == email,
            PasswordResetTokenModel.token == token,
        )
        .with_for_update(of=PasswordResetTokenModel)
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


async def activate_user(
    db: AsyncSession,
    email: str,
    token: str,
) -> None:
    try:
        email = accounts_validators.validate_email(email)

        user = await get_user_by_email_for_update(
            db=db,
            email=email,
        )

        if user is None:
            raise InvalidActivationTokenError()

        token_record = await get_activation_token(
            db=db,
            email=email,
            token=token,
        )

        if token_record is None:
            raise InvalidActivationTokenError()

        token_expires_at = get_token_expires_at(token_record)

        if token_expires_at <= datetime.now(timezone.utc):
            await db.delete(token_record)
            await db.commit()

            raise InvalidActivationTokenError()

        if user.is_active:
            raise UserAlreadyActiveError()

        user.is_active = True
        await db.delete(token_record)

        await db.commit()

    except Exception:
        await db.rollback()
        raise


async def renew_activation_token(
    db: AsyncSession,
    email: str,
) -> ActivationTokenModel | None:
    try:
        email = accounts_validators.validate_email(email)

        user = await get_user_by_email_for_update(
            db=db,
            email=email,
        )

        if user is None or user.is_active:
            await db.rollback()
            return None

        token_record = await get_activation_token_by_user_id(
            db=db,
            user_id=user.id,
        )

        now_utc = datetime.now(timezone.utc)

        if token_record is not None:
            if get_token_expires_at(token_record) > now_utc:
                await db.rollback()
                return None

            token_record.token = generate_secure_token()
            token_record.expires_at = now_utc + timedelta(days=1)

        else:
            token_record = ActivationTokenModel(
                user_id=user.id,
            )
            db.add(token_record)

        await db.commit()

        return token_record

    except Exception:
        await db.rollback()
        raise


async def login_user(
    db: AsyncSession,
    email: str,
    raw_password: str,
    jwt_manager: JWTAuthManagerInterface,
    refresh_token_days: int,
) -> tuple[str, str]:
    try:
        email = accounts_validators.validate_email(email)

        user = await get_user_by_email_for_update(
            db=db,
            email=email,
        )

        if user is None:
            raise InvalidCredentialsError()

        if not user.verify_password(raw_password):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise UserNotActiveError()

        data_to_encode = {"sub": str(user.id)}

        access_token = jwt_manager.create_access_token(
            data=data_to_encode,
        )
        refresh_token = jwt_manager.create_refresh_token(
            data=data_to_encode,
            expires_delta=timedelta(days=refresh_token_days),
        )

        refresh_token_record = RefreshTokenModel.create(
            user_id=user.id,
            days_valid=refresh_token_days,
            token=refresh_token,
        )
        db.add(refresh_token_record)

        await db.commit()

        return access_token, refresh_token

    except Exception:
        await db.rollback()
        raise


async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str,
    jwt_manager: JWTAuthManagerInterface,
) -> str:
    payload = jwt_manager.decode_refresh_token(
        token=refresh_token,
    )
    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject.isascii() or not subject.isdigit():
        raise InvalidTokenError(
            "Refresh token must contain a numeric user ID in the 'sub' claim."
        )

    user_id = int(subject)

    if user_id <= 0:
        raise InvalidTokenError(
            "User ID in the refresh token must be a positive integer."
        )

    token_record = await get_refresh_token(
        db=db,
        token=refresh_token,
    )

    if token_record is None:
        raise InvalidTokenError("Refresh token was not found or has been revoked.")

    if token_record.user_id != user_id:
        raise InvalidTokenError("Refresh token owner does not match its 'sub' claim.")

    if get_token_expires_at(token_record) <= datetime.now(timezone.utc):
        raise TokenExpiredError("Refresh token has expired.")

    user = token_record.user

    if user is None:
        raise InvalidTokenError(
            "The user associated with the refresh token no longer exists."
        )

    if not user.is_active:
        raise UserNotActiveError()

    return jwt_manager.create_access_token(
        data={"sub": str(user.id)},
    )


async def logout_user(
    db: AsyncSession,
    refresh_token: str,
) -> None:
    try:
        token_record = await get_refresh_token(
            db=db,
            token=refresh_token,
        )

        if token_record is None:
            await db.rollback()
            return

        await db.delete(token_record)
        await db.commit()

    except Exception:
        await db.rollback()
        raise


async def change_user_password(
    db: AsyncSession,
    user: UserModel,
    old_password: str,
    new_password: str,
) -> None:
    try:
        user_id = user.id

        user = await get_user_by_id_for_update(
            db=db,
            user_id=user_id,
        )

        if user is None:
            raise UserNotFoundError(f"User with ID {user_id} was not found.")

        if not user.is_active:
            raise UserNotActiveError()

        if not user.verify_password(old_password):
            raise InvalidPasswordError()

        if user.verify_password(new_password):
            raise PasswordUnchangedError()

        user.password = new_password

        await db.execute(
            delete(RefreshTokenModel).where(
                RefreshTokenModel.user_id == user.id,
            )
        )

        await db.execute(
            delete(PasswordResetTokenModel).where(
                PasswordResetTokenModel.user_id == user.id,
            )
        )

        await db.commit()

    except Exception:
        await db.rollback()
        raise


async def request_password_reset(
    db: AsyncSession,
    email: str,
) -> PasswordResetTokenModel | None:
    try:
        email = accounts_validators.validate_email(email)

        user = await get_user_by_email_for_update(
            db=db,
            email=email,
        )

        if user is None or not user.is_active:
            await db.rollback()
            return None

        token_record = await get_password_reset_token_by_user_id(
            db=db,
            user_id=user.id,
        )

        now_utc = datetime.now(timezone.utc)

        if token_record is not None:
            if get_token_expires_at(token_record) > now_utc:
                await db.rollback()
                return None

            token_record.token = generate_secure_token()
            token_record.expires_at = now_utc + timedelta(days=1)

        else:
            token_record = PasswordResetTokenModel(
                user_id=user.id,
            )
            db.add(token_record)

        await db.commit()

        return token_record

    except Exception:
        await db.rollback()
        raise


async def reset_user_password(
    db: AsyncSession,
    email: str,
    token: str,
    new_password: str,
) -> None:
    try:
        email = accounts_validators.validate_email(email)

        user = await get_user_by_email_for_update(
            db=db,
            email=email,
        )

        if user is None or not user.is_active:
            raise InvalidPasswordResetTokenError()

        token_record = await get_password_reset_token(
            db=db,
            email=email,
            token=token,
        )

        if token_record is None:
            raise InvalidPasswordResetTokenError()

        token_expires_at = get_token_expires_at(token_record)

        if token_expires_at <= datetime.now(timezone.utc):
            await db.delete(token_record)
            await db.commit()

            raise InvalidPasswordResetTokenError()

        if user.verify_password(new_password):
            raise PasswordUnchangedError()

        user.password = new_password

        await db.delete(token_record)

        await db.execute(
            delete(RefreshTokenModel).where(
                RefreshTokenModel.user_id == user.id,
            )
        )

        await db.commit()

    except Exception:
        await db.rollback()
        raise


async def activate_user_by_admin(
    db: AsyncSession,
    user_id: int,
) -> None:
    try:
        user = await get_user_by_id_for_update(
            db=db,
            user_id=user_id,
        )

        if user is None:
            raise UserNotFoundError(f"User with ID {user_id} was not found.")

        if user.is_active:
            raise UserAlreadyActiveError()

        user.is_active = True

        await db.execute(
            delete(ActivationTokenModel).where(
                ActivationTokenModel.user_id == user_id,
            )
        )

        await db.commit()

    except Exception:
        await db.rollback()
        raise
