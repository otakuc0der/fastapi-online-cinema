import uuid
from datetime import datetime, timedelta, timezone

from jose import ExpiredSignatureError, JWTError, JWSError, jwt

from exceptions import (
    InvalidTokenError,
    TokenCreationError,
    TokenExpiredError,
)
from security.interfaces import JWTAuthManagerInterface


class JWTAuthManager(JWTAuthManagerInterface):
    _ACCESS_KEY_TIMEDELTA_MINUTES = timedelta(minutes=30)
    _REFRESH_KEY_TIMEDELTA_MINUTES = timedelta(days=7)

    def __init__(self, secret_key_access: str, secret_key_refresh: str, algorithm: str):
        self._secret_key_access = secret_key_access
        self._secret_key_refresh = secret_key_refresh
        self._algorithm = algorithm

    def _create_token(
        self,
        data_to_encode: dict,
        secret_key: str,
        expires_delta: timedelta,
    ) -> str:
        payload = {
            **data_to_encode,
            "exp": datetime.now(timezone.utc) + expires_delta,
            "jti": str(uuid.uuid4()),
        }

        return jwt.encode(
            payload,
            secret_key,
            algorithm=self._algorithm,
        )

    def create_access_token(
        self,
        data: dict,
        expires_delta: timedelta | None = None,
    ) -> str:
        data_to_encode = {
            **data,
            "type": "access",
        }

        try:
            return self._create_token(
                data_to_encode,
                self._secret_key_access,
                expires_delta=(
                    self._ACCESS_KEY_TIMEDELTA_MINUTES
                    if expires_delta is None
                    else expires_delta
                ),
            )
        except JWSError as error:
            raise TokenCreationError() from error

    def create_refresh_token(
        self,
        data: dict,
        expires_delta: timedelta | None = None,
    ) -> str:
        data_to_encode = {
            **data,
            "type": "refresh",
        }

        try:
            return self._create_token(
                data_to_encode,
                self._secret_key_refresh,
                expires_delta=(
                    self._REFRESH_KEY_TIMEDELTA_MINUTES
                    if expires_delta is None
                    else expires_delta
                ),
            )
        except JWSError as error:
            raise TokenCreationError() from error

    def decode_access_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                self._secret_key_access,
                algorithms=[self._algorithm],
                options={"require_exp": True},
            )
        except ExpiredSignatureError as error:
            raise TokenExpiredError() from error
        except JWTError as error:
            raise InvalidTokenError() from error

        if payload.get("type") != "access":
            raise InvalidTokenError()

        return payload

    def decode_refresh_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                self._secret_key_refresh,
                algorithms=[self._algorithm],
                options={"require_exp": True},
            )
        except ExpiredSignatureError as error:
            raise TokenExpiredError() from error
        except JWTError as error:
            raise InvalidTokenError() from error

        if payload.get("type") != "refresh":
            raise InvalidTokenError()

        return payload

    def verify_access_token_or_raise(self, token: str) -> None:
        self.decode_access_token(token)

    def verify_refresh_token_or_raise(self, token: str) -> None:
        self.decode_refresh_token(token)
