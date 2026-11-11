import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_jwt_auth_manager, get_settings
from config.settings import Settings
from database import UserModel, get_db
from exceptions import (
    InvalidActivationTokenError,
    InvalidCredentialsError,
    InvalidPasswordError,
    InvalidTokenError,
    PasswordUnchangedError,
    TokenExpiredError,
    UserAlreadyActiveError,
    UserAlreadyExistsError,
    UserGroupNotFoundError,
    UserNotActiveError,
    UserNotFoundError,
)
from schemas.accounts import (
    MessageResponseSchema,
    PasswordChangeRequestSchema,
    PasswordResetRequestSchema,
    TokenRefreshRequestSchema,
    TokenRefreshResponseSchema,
    UserActivationRequestSchema,
    UserActivationResendRequestSchema,
    UserCurrentResponseSchema,
    UserLoginRequestSchema,
    UserLoginResponseSchema,
    UserLogoutRequestSchema,
    UserRegistrationRequestSchema,
    UserRegistrationResponseSchema,
)
from security.dependencies import get_current_user
from security.interfaces import JWTAuthManagerInterface
from services.account_crud import (
    activate_user,
    change_user_password,
    login_user as login_user_service,
    logout_user,
    refresh_access_token,
    register_user,
    renew_activation_token,
    request_password_reset as request_password_reset_service,
)

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


@router.post(
    "/activate/resend/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def resend_activation(
    resend_data: UserActivationResendRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    try:
        await renew_activation_token(
            db=db,
            email=str(resend_data.email),
        )

        return MessageResponseSchema(
            message=(
                "If the account requires activation, " "the request has been processed."
            )
        )

    except Exception as error:
        logger.exception("Failed to renew activation token")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while requesting account activation.",
        ) from error


@router.post(
    "/login/",
    response_model=UserLoginResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def login_user(
    login_data: UserLoginRequestSchema,
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    settings: Settings = Depends(get_settings),
) -> UserLoginResponseSchema:
    try:
        access_token, refresh_token = await login_user_service(
            db=db,
            email=str(login_data.email),
            raw_password=login_data.password,
            jwt_manager=jwt_manager,
            refresh_token_days=settings.REFRESH_TOKEN_DAYS,
        )

        return UserLoginResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error

    except UserNotActiveError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception("Failed to log in user")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login.",
        ) from error


@router.post(
    "/refresh/",
    response_model=TokenRefreshResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def refresh_token(
    refresh_token_data: TokenRefreshRequestSchema,
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
) -> TokenRefreshResponseSchema:
    try:
        access_token = await refresh_access_token(
            db=db,
            refresh_token=refresh_token_data.refresh_token,
            jwt_manager=jwt_manager,
        )

        return TokenRefreshResponseSchema(
            access_token=access_token,
        )

    except TokenExpiredError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired.",
        ) from error

    except InvalidTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        ) from error

    except UserNotActiveError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception("Failed to refresh access token")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while refreshing the access token.",
        ) from error


@router.post(
    "/logout/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def logout(
    logout_data: UserLogoutRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    try:
        await logout_user(
            db=db,
            refresh_token=logout_data.refresh_token,
        )

        return MessageResponseSchema(message="User logged out successfully.")

    except Exception as error:
        logger.exception("Failed to log out user")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout.",
        ) from error


@router.get(
    "/me/",
    response_model=UserCurrentResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_current_account(
    user: UserModel = Depends(get_current_user),
) -> UserCurrentResponseSchema:
    return UserCurrentResponseSchema.model_validate(user)


@router.post(
    "/password/change/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def change_password(
    password_data: PasswordChangeRequestSchema,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    try:
        await change_user_password(
            db=db,
            user=user,
            old_password=password_data.old_password,
            new_password=password_data.new_password,
        )

        return MessageResponseSchema(
            message="Password changed successfully. Please log in again."
        )

    except (InvalidPasswordError, PasswordUnchangedError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

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

    except Exception as error:
        logger.exception("Failed to change user password")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while changing the password.",
        ) from error


@router.post(
    "/password/reset/request/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def request_password_reset(
    password_reset_data: PasswordResetRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    try:
        await request_password_reset_service(
            db=db,
            email=str(password_reset_data.email),
        )

        return MessageResponseSchema(
            message=(
                "If the account exists and is active, "
                "the password reset request has been processed."
            )
        )

    except Exception as error:
        logger.exception("Failed to request password reset")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while requesting a password reset.",
        ) from error
