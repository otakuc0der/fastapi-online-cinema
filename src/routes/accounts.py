import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from exceptions import (
    InvalidActivationTokenError,
    UserAlreadyActiveError,
    UserAlreadyExistsError,
    UserGroupNotFoundError,
)
from schemas.accounts import (
    MessageResponseSchema,
    UserActivationRequestSchema,
    UserRegistrationRequestSchema,
    UserRegistrationResponseSchema,
)
from services.account_crud import activate_user, register_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register/",
    response_model=UserRegistrationResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: UserRegistrationRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> UserRegistrationResponseSchema:
    try:
        user, _ = await register_user(
            db=db,
            email=str(user_data.email),
            raw_password=user_data.password,
        )

        return UserRegistrationResponseSchema.model_validate(user)

    except UserAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except UserGroupNotFoundError as error:
        logger.exception("Default user group is missing")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during user creation.",
        ) from error

    except Exception as error:
        logger.exception("Failed to register user")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during user creation.",
        ) from error


@router.post(
    "/activate/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def activate_account(
    activation_data: UserActivationRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    try:
        await activate_user(
            db=db,
            email=str(activation_data.email),
            token=activation_data.token,
        )

        return MessageResponseSchema(message="User account activated successfully.")

    except (InvalidActivationTokenError, UserAlreadyActiveError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception("Failed to activate user account")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during account activation.",
        ) from error
