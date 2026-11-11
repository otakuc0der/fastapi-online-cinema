import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_jwt_auth_manager
from database import UserModel, get_db
from exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    UserNotActiveError,
)
from security.http import get_token
from security.interfaces import JWTAuthManagerInterface
from services.account_crud import get_user_by_id

logger = logging.getLogger(__name__)


async def get_current_user(
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
) -> UserModel:
    try:
        payload = jwt_manager.decode_access_token(token)
        subject = payload.get("sub")

        if (
            not isinstance(subject, str)
            or not subject.isascii()
            or not subject.isdigit()
        ):
            raise InvalidTokenError(
                "Access token must contain a numeric user ID in the 'sub' claim."
            )

        user_id = int(subject)

        if user_id <= 0:
            raise InvalidTokenError(
                "User ID in the access token must be a positive integer."
            )

        user = await get_user_by_id(
            db=db,
            user_id=user_id,
        )

        if user is None:
            raise InvalidTokenError(
                "The user associated with the access token no longer exists."
            )

        if not user.is_active:
            raise UserNotActiveError("User account is not activated.")

        return user

    except TokenExpiredError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    except InvalidTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    except UserNotActiveError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception("Failed to authenticate user")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during authentication.",
        ) from error
