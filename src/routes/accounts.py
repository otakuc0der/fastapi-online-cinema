import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    HTTPException,
    Path,
    Request,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from config import (
    get_accounts_email_notificator,
    get_jwt_auth_manager,
    get_settings,
)
from config.settings import BaseAppSettings, Settings
from database import UserModel, get_db
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
from notifications import EmailSenderInterface
from routes.utils import build_url
from schemas.accounts import (
    MessageResponseSchema,
    PasswordChangeRequestSchema,
    PasswordResetCompleteRequestSchema,
    PasswordResetRequestSchema,
    TokenRefreshRequestSchema,
    TokenRefreshResponseSchema,
    UserActivationRequestSchema,
    UserActivationResendRequestSchema,
    UserCurrentResponseSchema,
    UserGroupUpdateRequestSchema,
    UserLoginRequestSchema,
    UserLoginResponseSchema,
    UserLogoutRequestSchema,
    UserRegistrationRequestSchema,
    UserRegistrationResponseSchema,
)
from schemas.examples.accounts import (
    ACTIVATE_ACCOUNT_REQUEST_EXAMPLES,
    ACTIVATE_ACCOUNT_RESPONSES,
    ADMIN_ACTIVATE_ACCOUNT_RESPONSES,
    ADMIN_CHANGE_GROUP_REQUEST_EXAMPLES,
    ADMIN_CHANGE_GROUP_RESPONSES,
    CHANGE_PASSWORD_REQUEST_EXAMPLES,
    CHANGE_PASSWORD_RESPONSES,
    GET_CURRENT_ACCOUNT_RESPONSES,
    LOGIN_REQUEST_EXAMPLES,
    LOGIN_RESPONSES,
    LOGOUT_REQUEST_EXAMPLES,
    LOGOUT_RESPONSES,
    REFRESH_TOKEN_REQUEST_EXAMPLES,
    REFRESH_TOKEN_RESPONSES,
    REGISTER_REQUEST_EXAMPLES,
    REGISTER_RESPONSES,
    REQUEST_PASSWORD_RESET_REQUEST_EXAMPLES,
    REQUEST_PASSWORD_RESET_RESPONSES,
    RESEND_ACTIVATION_REQUEST_EXAMPLES,
    RESEND_ACTIVATION_RESPONSES,
    RESET_PASSWORD_REQUEST_EXAMPLES,
    RESET_PASSWORD_RESPONSES,
)
from security.dependencies import get_current_admin, get_current_user
from security.interfaces import JWTAuthManagerInterface
from services.account_crud import (
    activate_user,
    activate_user_by_admin,
    change_user_group,
    change_user_password,
    login_user as login_user_service,
    logout_user,
    refresh_access_token,
    register_user,
    renew_activation_token,
    request_password_reset as request_password_reset_service,
    reset_user_password,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register/",
    response_model=UserRegistrationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register an account",
    description=(
        "Register using an email and password. The email must be unique and the "
        "password must satisfy the request schema validation. The new account "
        "requires activation before login. A 24-hour activation token is created "
        "and activation email sending is scheduled using BackgroundTasks.\n\nThe "
        "email link carries the token as a query parameter. The activation API "
        "accepts email and token in a JSON POST body, opening the email link does "
        "not itself perform this POST. Email delivery takes place after the "
        "response, a successful registration response is not a delivery receipt."
    ),
    response_description="Created user account, activation email sending scheduled.",
    responses=REGISTER_RESPONSES,
)
async def register(
    request: Request,
    background_tasks: BackgroundTasks,
    user_data: Annotated[
        UserRegistrationRequestSchema,
        Body(openapi_examples=REGISTER_REQUEST_EXAMPLES),
    ],
    db: AsyncSession = Depends(get_db),
    settings: BaseAppSettings = Depends(get_settings),
    email_notificator: EmailSenderInterface = Depends(get_accounts_email_notificator),
) -> UserRegistrationResponseSchema:
    try:
        user, activation_token = await register_user(
            db=db,
            email=str(user_data.email),
            raw_password=user_data.password,
        )

        activation_link = build_url(
            request=request,
            base_url=settings.BASE_URL,
            route_name="activate_account",
            token=activation_token.token,
        )

        background_tasks.add_task(
            email_notificator.send_activation_email,
            email=user.email,
            activation_link=activation_link,
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
    summary="Activate an account",
    description=(
        "Activate an account using its email and activation token in an "
        "application/json request body. A valid unexpired token is required, "
        "activation tokens are valid for 24 hours after issuance. The service "
        "activates the account and consumes the token. Invalid or expired tokens "
        "and already active accounts return 400.\n\nAfter successful activation, "
        "confirmation email sending is scheduled in BackgroundTasks. No Bearer "
        "access token is required."
    ),
    response_description="Account activation confirmation.",
    responses=ACTIVATE_ACCOUNT_RESPONSES,
)
async def activate_account(
    request: Request,
    activation_data: Annotated[
        UserActivationRequestSchema,
        Body(openapi_examples=ACTIVATE_ACCOUNT_REQUEST_EXAMPLES),
    ],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    settings: BaseAppSettings = Depends(get_settings),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
) -> MessageResponseSchema:
    try:
        email = str(activation_data.email)

        await activate_user(
            db=db,
            email=email,
            token=activation_data.token,
        )

        background_tasks.add_task(
            email_sender.send_activation_complete_email,
            email=email,
            login_link=build_url(
                request=request, base_url=settings.BASE_URL, route_name="login_user"
            ),
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
    summary="Request a new activation link",
    description=(
        "Submit an email to request renewal of an activation token. This supports "
        "requesting a new link after the previous token expires. When the service "
        "issues a new token, it is valid for another 24 hours and an activation "
        "email is scheduled. If the service returns no token, no email is "
        "scheduled.\n\nThe same success message is returned without confirming that "
        "an account exists, requires activation or received a new email. No Bearer "
        "access token is required. Scheduled email delivery runs after the "
        "response."
    ),
    response_description="Generic activation request confirmation.",
    responses=RESEND_ACTIVATION_RESPONSES,
)
async def resend_activation(
    request: Request,
    background_tasks: BackgroundTasks,
    resend_data: Annotated[
        UserActivationResendRequestSchema,
        Body(openapi_examples=RESEND_ACTIVATION_REQUEST_EXAMPLES),
    ],
    db: AsyncSession = Depends(get_db),
    settings: BaseAppSettings = Depends(get_settings),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
) -> MessageResponseSchema:
    try:
        email = str(resend_data.email)

        activation_token = await renew_activation_token(
            db=db,
            email=email,
        )

        if activation_token is not None:
            activation_link = build_url(
                request=request,
                base_url=settings.BASE_URL,
                route_name="activate_account",
                token=activation_token.token,
            )

            background_tasks.add_task(
                email_sender.send_activation_email,
                email=email,
                activation_link=activation_link,
            )

        return MessageResponseSchema(
            message=(
                "If the account requires activation, the request has been processed."
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
    summary="Log in",
    description=(
        "Authenticate using email and password in an application/json body. The "
        "account must be active. A successful login returns an access token and a "
        "refresh token. Use the access token in Authorization: Bearer <token> for "
        "protected endpoints. Use the refresh token in the refresh request body to "
        "obtain a new access token. Access token lifetime is shorter than refresh "
        "token lifetime, exact lifetimes are configured by the "
        "application.\n\nInvalid credentials return 401. An inactive account returns "
        "403. This endpoint does not require an existing Bearer token."
    ),
    response_description="Access and refresh token pair.",
    responses=LOGIN_RESPONSES,
)
async def login_user(
    login_data: Annotated[
        UserLoginRequestSchema,
        Body(openapi_examples=LOGIN_REQUEST_EXAMPLES),
    ],
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
    summary="Refresh an access token",
    description=(
        "Provide a refresh token in an application/json body to obtain a new access "
        "token without resubmitting the password. The refresh token must be valid, "
        "unexpired and accepted by the token service, and its account must be "
        "active. Only an access token is returned, this endpoint does not return a "
        "rotated refresh token. No Bearer access token is required. Invalid or "
        "expired refresh tokens return 401."
    ),
    response_description="New access token.",
    responses=REFRESH_TOKEN_RESPONSES,
)
async def refresh_token(
    refresh_token_data: Annotated[
        TokenRefreshRequestSchema,
        Body(openapi_examples=REFRESH_TOKEN_REQUEST_EXAMPLES),
    ],
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
    summary="Log out",
    description=(
        "Provide the refresh token in an application/json body. The service revokes "
        "the stored refresh token so it cannot be used to obtain new access tokens. "
        "This controller has no Bearer access-token dependency.\n\nRevoking a refresh "
        "token does not immediately invalidate an already issued access token, that "
        "token remains subject to its own expiration. Clients should discard their "
        "locally stored tokens on logout."
    ),
    response_description="Logout confirmation.",
    responses=LOGOUT_RESPONSES,
)
async def logout(
    logout_data: Annotated[
        UserLogoutRequestSchema,
        Body(openapi_examples=LOGOUT_REQUEST_EXAMPLES),
    ],
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
    summary="Get the current account",
    description=(
        "Return the current active user identified by a valid Bearer access token. "
        "No user ID or request body is required. The exact response fields are "
        "defined by UserCurrentResponseSchema. Missing, malformed, invalid or "
        "expired access credentials are rejected by authentication, inactive "
        "accounts are forbidden."
    ),
    response_description="Authenticated account details.",
    responses=GET_CURRENT_ACCOUNT_RESPONSES,
)
async def get_current_account(
    user: UserModel = Depends(get_current_user),
) -> UserCurrentResponseSchema:
    return UserCurrentResponseSchema.model_validate(user)


@router.post(
    "/password/change/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Change the current password",
    description=(
        "Change the authenticated active user's password by supplying old_password "
        "and new_password in an application/json body. The old password must be "
        "correct and the new password must differ from the current one and satisfy "
        "password validation. A valid Bearer access token is required.\n\nExisting "
        "refresh tokens are revoked by the password-change service. Log in again "
        "using the new password. This controller does not schedule a "
        "password-change email."
    ),
    response_description="Password change confirmation.",
    responses=CHANGE_PASSWORD_RESPONSES,
)
async def change_password(
    password_data: Annotated[
        PasswordChangeRequestSchema,
        Body(openapi_examples=CHANGE_PASSWORD_REQUEST_EXAMPLES),
    ],
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
    summary="Request a password reset",
    description=(
        "Submit an email in an application/json body. If the service issues a reset "
        "token for an existing active account, password reset email sending is "
        "scheduled using BackgroundTasks. If the service returns no token, no email "
        "is scheduled.\n\nThe same success message is returned without revealing "
        "whether an active account exists or a new reset token was issued. No "
        "Bearer access token or old password is required. Opening the emailed link "
        "does not itself change the password, complete the reset through the "
        "separate POST endpoint. A successful response is not an email delivery "
        "receipt."
    ),
    response_description="Generic password reset request confirmation.",
    responses=REQUEST_PASSWORD_RESET_RESPONSES,
)
async def request_password_reset(
    request: Request,
    background_tasks: BackgroundTasks,
    password_reset_data: Annotated[
        PasswordResetRequestSchema,
        Body(openapi_examples=REQUEST_PASSWORD_RESET_REQUEST_EXAMPLES),
    ],
    db: AsyncSession = Depends(get_db),
    settings: BaseAppSettings = Depends(get_settings),
    email_notificator: EmailSenderInterface = Depends(get_accounts_email_notificator),
) -> MessageResponseSchema:
    try:
        email = str(password_reset_data.email)

        reset_token = await request_password_reset_service(
            db=db,
            email=email,
        )

        if reset_token is not None:
            reset_link = build_url(
                request=request,
                base_url=settings.BASE_URL,
                route_name="reset_password",
                token=reset_token.token,
            )

            background_tasks.add_task(
                email_notificator.send_password_reset_email,
                email=email,
                reset_link=reset_link,
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


@router.post(
    "/password/reset/complete/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Complete a password reset",
    description=(
        "Submit email, token and password in an application/json body. Use the "
        "password reset token from the email. The service checks the account and "
        "token, including expiration, before setting the new password. The new "
        "password must differ from the current one and satisfy password validation. "
        "No old password or Bearer access token is required.\n\nAfter a successful "
        "reset the reset token is consumed, existing refresh tokens are revoked, "
        "and confirmation email sending is scheduled in BackgroundTasks. Log in "
        "using the new password."
    ),
    response_description="Password reset confirmation.",
    responses=RESET_PASSWORD_RESPONSES,
)
async def reset_password(
    request: Request,
    background_tasks: BackgroundTasks,
    password_data: Annotated[
        PasswordResetCompleteRequestSchema,
        Body(openapi_examples=RESET_PASSWORD_REQUEST_EXAMPLES),
    ],
    db: AsyncSession = Depends(get_db),
    settings: BaseAppSettings = Depends(get_settings),
    email_notificator: EmailSenderInterface = Depends(get_accounts_email_notificator),
) -> MessageResponseSchema:
    try:
        await reset_user_password(
            db=db,
            email=str(password_data.email),
            token=password_data.token,
            new_password=password_data.password,
        )

        background_tasks.add_task(
            email_notificator.send_password_reset_complete_email,
            email=str(password_data.email),
            login_link=build_url(
                request=request, base_url=settings.BASE_URL, route_name="login_user"
            ),
        )

        return MessageResponseSchema(
            message="Password reset successfully. Please log in."
        )

    except (
        InvalidPasswordResetTokenError,
        PasswordUnchangedError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception("Failed to reset user password")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while resetting the password.",
        ) from error


@router.post(
    "/admin/users/{user_id}/activate/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Activate an account as an administrator",
    description=(
        "Manually activate the account identified by user_id without requiring an "
        "activation token. A valid Bearer access token for an active administrator "
        "is required. A missing user returns 404, an already active account returns "
        "400. This controller does not schedule an activation confirmation email."
    ),
    response_description="Administrator account activation confirmation.",
    responses=ADMIN_ACTIVATE_ACCOUNT_RESPONSES,
)
async def admin_activate_account(
    user_id: Annotated[
        int,
        Path(ge=1, description="ID of the user to manage.", examples=[17]),
    ],
    admin: UserModel = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    admin_id = admin.id

    try:
        await activate_user_by_admin(
            db=db,
            user_id=user_id,
        )

        return MessageResponseSchema(message="User account activated successfully.")

    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except UserAlreadyActiveError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "Administrator %s failed to activate user %s",
            admin_id,
            user_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during account activation.",
        ) from error


@router.patch(
    "/admin/users/{user_id}/group/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Change a user group as an administrator",
    description=(
        "Set the group of the user identified by user_id. Send group in an "
        "application/json body using user, moderator or admin. A valid Bearer "
        "access token for an active administrator is required. A missing target "
        "user returns 404. A valid group that is missing from the database is "
        "treated as a server configuration error and returns 500. This endpoint "
        "changes group membership and does not schedule an email."
    ),
    response_description="User group update confirmation.",
    responses=ADMIN_CHANGE_GROUP_RESPONSES,
)
async def admin_change_user_group(
    user_id: Annotated[
        int,
        Path(ge=1, description="ID of the user to manage.", examples=[17]),
    ],
    group_data: Annotated[
        UserGroupUpdateRequestSchema,
        Body(openapi_examples=ADMIN_CHANGE_GROUP_REQUEST_EXAMPLES),
    ],
    admin: UserModel = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    admin_id = admin.id

    try:
        await change_user_group(
            db=db,
            user_id=user_id,
            group_name=group_data.group,
        )

        return MessageResponseSchema(message="User group updated successfully.")

    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except UserGroupNotFoundError as error:
        logger.exception(
            "Required user group '%s' is missing",
            group_data.group.value,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the user group.",
        ) from error

    except Exception as error:
        logger.exception(
            "Administrator %s failed to update group for user %s",
            admin_id,
            user_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the user group.",
        ) from error
