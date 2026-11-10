from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from database import accounts_validators


class UserBaseSchema(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, email: object) -> str:
        if not isinstance(email, str):
            raise ValueError("Email must be a string.")

        return accounts_validators.validate_email(email)


class UserRegistrationRequestSchema(UserBaseSchema):
    model_config = ConfigDict(extra="forbid")

    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        return accounts_validators.validate_password_strength(password)


class UserRegistrationResponseSchema(UserBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int


class MessageResponseSchema(BaseModel):
    message: str


class UserActivationRequestSchema(UserBaseSchema):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=1)


class PasswordResetRequestSchema(UserBaseSchema):
    model_config = ConfigDict(extra="forbid")


class UserActivationResendRequestSchema(UserBaseSchema):
    model_config = ConfigDict(extra="forbid")


class PasswordChangeRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, new_password: str) -> str:
        return accounts_validators.validate_password_strength(new_password)


class PasswordResetCompleteRequestSchema(UserRegistrationRequestSchema):
    token: str = Field(min_length=1)


class UserLoginRequestSchema(UserBaseSchema):
    model_config = ConfigDict(extra="forbid")

    password: str


class UserLoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenBaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=1)


class TokenRefreshRequestSchema(RefreshTokenBaseSchema):
    pass


class TokenRefreshResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserLogoutRequestSchema(RefreshTokenBaseSchema):
    pass
