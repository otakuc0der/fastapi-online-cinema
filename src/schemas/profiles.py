from datetime import date

from fastapi import File, Form, UploadFile
from fastapi.exceptions import RequestValidationError
from pydantic import (
    BaseModel,
    ConfigDict,
    HttpUrl,
    ValidationError,
    field_validator,
)

from database.models.accounts import GenderEnum
from validators.profile import (
    validate_avatar,
    validate_date_of_birth,
    validate_info,
    validate_name,
)


class ProfileBaseSchema(BaseModel):
    first_name: str
    last_name: str
    gender: GenderEnum
    date_of_birth: date
    info: str

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        validate_name(name=value)
        return value.lower()

    @field_validator("info")
    @classmethod
    def validate_info(cls, value: str) -> str:
        validate_info(info=value)
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, date_of_birth: date) -> date:
        validate_date_of_birth(birth_date=date_of_birth)
        return date_of_birth


class ProfileRequestSchema(ProfileBaseSchema):
    model_config = ConfigDict(extra="forbid")

    avatar: UploadFile | None = None

    @field_validator("avatar")
    @classmethod
    def validate_avatar(cls, avatar: UploadFile | None) -> UploadFile | None:
        if avatar is not None:
            validate_avatar(avatar)

        return avatar

    @classmethod
    def as_form(
        cls,
        first_name: str = Form(...),
        last_name: str = Form(...),
        gender: GenderEnum = Form(...),
        date_of_birth: date = Form(...),
        info: str = Form(...),
        avatar: UploadFile | None = File(None),
    ) -> "ProfileRequestSchema":
        try:
            return cls(
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=date_of_birth,
                info=info,
                avatar=avatar,
            )
        except ValidationError as error:
            errors = error.errors(
                include_input=False,
                include_context=False,
                include_url=False,
            )
            for err in errors:
                if "avatar" in err["loc"]:
                    err["loc"] = "body", *err["loc"]

            raise RequestValidationError(errors) from error


class ProfileResponseSchema(ProfileBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    avatar: HttpUrl | None = None


class ProfileUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str | None = None
    last_name: str | None = None
    gender: GenderEnum | None = None
    date_of_birth: date | None = None
    info: str | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Name cannot be null.")
        validate_name(name=value)
        return value.lower()

    @field_validator("info")
    @classmethod
    def validate_info(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Info cannot be null.")
        validate_info(info=value)
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, date_of_birth: date | None) -> date:
        if date_of_birth is None:
            raise ValueError("Date of birth cannot be null.")
        validate_date_of_birth(birth_date=date_of_birth)
        return date_of_birth

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: GenderEnum | None) -> GenderEnum:
        if value is None:
            raise ValueError("Gender cannot be null.")
        return value


class ProfileAvatarUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    avatar: UploadFile

    @field_validator("avatar")
    @classmethod
    def validate_avatar(cls, avatar: UploadFile) -> UploadFile:
        validate_avatar(avatar)
        return avatar

    @classmethod
    def as_form(cls, avatar: UploadFile = File(...)) -> "ProfileAvatarUpdateSchema":
        try:
            return cls(avatar=avatar)
        except ValidationError as error:
            errors = error.errors(
                include_input=False,
                include_context=False,
                include_url=False,
            )

            for item in errors:
                item["loc"] = ("body", *item["loc"])

            raise RequestValidationError(errors) from error
