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
from schemas.genres import (
    GenreCreateSchema,
    GenreListItemSchema,
    GenreSchema,
    GenreUpdateSchema,
)
from schemas.movies import (
    MovieBaseSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)
from schemas.stars import (
    StarCreateSchema,
    StarListResponseSchema,
    StarSchema,
    StarUpdateSchema,
)
