from schemas.examples.security import moderator_error_responses

REGISTER_REQUEST_EXAMPLES = {
    "registration": {
        "summary": "Register with an email and password",
        "value": {
            "email": "user@example.com",
            "password": "Cinema!Pass2026",
        },
    },
}


ACTIVATE_ACCOUNT_REQUEST_EXAMPLES = {
    "activation": {
        "summary": "Activate using the email and token",
        "value": {
            "email": "user@example.com",
            "token": "activation-token-from-email",
        },
    },
}


RESEND_ACTIVATION_REQUEST_EXAMPLES = {
    "resend": {
        "summary": "Request a new activation link",
        "value": {
            "email": "user@example.com",
        },
    },
}


LOGIN_REQUEST_EXAMPLES = {
    "credentials": {
        "summary": "Log in to an activated account",
        "value": {
            "email": "user@example.com",
            "password": "Cinema!Pass2026",
        },
    },
}


REFRESH_TOKEN_REQUEST_EXAMPLES = {
    "refresh": {
        "summary": "Use the refresh token returned by login",
        "value": {
            "refresh_token": "refresh-token-from-login",
        },
    },
}


LOGOUT_REQUEST_EXAMPLES = {
    "logout": {
        "summary": "Revoke a refresh token",
        "value": {
            "refresh_token": "refresh-token-from-login",
        },
    },
}


CHANGE_PASSWORD_REQUEST_EXAMPLES = {
    "change_password": {
        "summary": "Change a known password",
        "value": {
            "old_password": "Cinema!Pass2026",
            "new_password": "NewCinema!Pass2026",
        },
    },
}


REQUEST_PASSWORD_RESET_REQUEST_EXAMPLES = {
    "request_reset": {
        "summary": "Request password reset instructions",
        "value": {
            "email": "user@example.com",
        },
    },
}


RESET_PASSWORD_REQUEST_EXAMPLES = {
    "complete_reset": {
        "summary": "Set a new password using the emailed token",
        "value": {
            "email": "user@example.com",
            "token": "password-reset-token-from-email",
            "password": "NewCinema!Pass2026",
        },
    },
}


ADMIN_CHANGE_GROUP_REQUEST_EXAMPLES = {
    "user": {
        "summary": "Assign the user group",
        "value": {
            "group": "user",
        },
    },
    "moderator": {
        "summary": "Assign the moderator group",
        "value": {
            "group": "moderator",
        },
    },
    "admin": {
        "summary": "Assign the administrator group",
        "value": {
            "group": "admin",
        },
    },
}


REGISTER_RESPONSES = {
    201: {
        "description": (
            "The account was created. Activation email sending was scheduled as a "
            "background task. The response fields are defined by "
            "UserRegistrationResponseSchema."
        ),
    },
    409: {
        "description": "A user with the supplied email already exists.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
            },
        },
    },
    422: {
        "description": (
            "Invalid or missing request fields. Values must satisfy the request "
            "schema, including email format and password validation where "
            "applicable."
        ),
    },
    500: {
        "description": (
            "The account could not be created, the default group is missing, or "
            "activation email scheduling or response preparation failed."
        ),
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
                "example": {
                    "detail": "An error occurred during user creation.",
                },
            },
        },
    },
}


ACTIVATE_ACCOUNT_RESPONSES = {
    200: {
        "description": "The account was activated and confirmation email sending was scheduled.",
        "content": {
            "application/json": {
                "example": {
                    "message": "User account activated successfully.",
                },
            },
        },
    },
    400: {
        "description": (
            "The activation token is invalid or expired, does not match the "
            "supplied email, or the account is already active."
        ),
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
            },
        },
    },
    422: {
        "description": (
            "Invalid or missing request fields. Values must satisfy the request "
            "schema, including email format and password validation where "
            "applicable."
        ),
    },
    500: {
        "description": "An error occurred during activation or confirmation email scheduling.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
                "example": {
                    "detail": "An error occurred during account activation.",
                },
            },
        },
    },
}


RESEND_ACTIVATION_RESPONSES = {
    200: {
        "description": (
            "The request was processed. The message does not confirm account "
            "existence or guarantee that a new email was scheduled."
        ),
        "content": {
            "application/json": {
                "example": {
                    "message": (
                        "If the account requires activation, the request has been "
                        "processed."
                    ),
                },
            },
        },
    },
    422: {
        "description": (
            "Invalid or missing request fields. Values must satisfy the request "
            "schema, including email format and password validation where "
            "applicable."
        ),
    },
    500: {
        "description": "The activation request could not be processed.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
                "example": {
                    "detail": "An error occurred while requesting account activation.",
                },
            },
        },
    },
}


LOGIN_RESPONSES = {
    200: {
        "description": (
            "An access token and refresh token were issued. Token examples are "
            "placeholders, not usable credentials."
        ),
        "content": {
            "application/json": {
                "example": {
                    "access_token": "access-token-from-login",
                    "refresh_token": "refresh-token-from-login",
                },
            },
        },
    },
    401: {
        "description": "The supplied email or password is incorrect.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
            },
        },
    },
    403: {
        "description": "The user account is not activated.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
                "example": {
                    "detail": "User account is not activated.",
                },
            },
        },
    },
    422: {
        "description": (
            "Invalid or missing request fields. Values must satisfy the request "
            "schema, including email format and password validation where "
            "applicable."
        ),
    },
    500: {
        "description": "The login request could not be processed.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
                "example": {
                    "detail": "An error occurred during login.",
                },
            },
        },
    },
}


REFRESH_TOKEN_RESPONSES = {
    200: {
        "description": (
            "A new access token was issued. No replacement refresh token is "
            "returned. The example is a placeholder."
        ),
        "content": {
            "application/json": {
                "example": {
                    "access_token": "new-access-token",
                },
            },
        },
    },
    401: {
        "description": "The refresh token is invalid, expired or no longer accepted.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
                "examples": {
                    "expired_refresh_token": {
                        "summary": "Refresh token has expired",
                        "value": {
                            "detail": "Refresh token has expired.",
                        },
                    },
                    "invalid_refresh_token": {
                        "summary": "Refresh token is invalid or revoked",
                        "value": {
                            "detail": "Invalid refresh token.",
                        },
                    },
                },
            },
        },
    },
    403: {
        "description": "The user account is not activated.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
                "example": {
                    "detail": "User account is not activated.",
                },
            },
        },
    },
    422: {
        "description": (
            "Invalid or missing request fields. Values must satisfy the request "
            "schema, including email format and password validation where "
            "applicable."
        ),
    },
    500: {
        "description": "The access token could not be refreshed.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
                "example": {
                    "detail": "An error occurred while refreshing the access token.",
                },
            },
        },
    },
}


LOGOUT_RESPONSES = {
    200: {
        "description": "Logout completed for the supplied refresh token.",
        "content": {
            "application/json": {
                "example": {
                    "message": "User logged out successfully.",
                },
            },
        },
    },
    422: {
        "description": (
            "Invalid or missing request fields. Values must satisfy the request "
            "schema, including email format and password validation where "
            "applicable."
        ),
    },
    500: {
        "description": "The logout request could not be processed.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
                "example": {
                    "detail": "An error occurred during logout.",
                },
            },
        },
    },
}


GET_CURRENT_ACCOUNT_RESPONSES = {
    200: {
        "description": (
            "The authenticated active account is returned. Response fields are "
            "defined by UserCurrentResponseSchema."
        ),
    },
    401: moderator_error_responses[401],
    403: {
        "description": "The user account is not activated.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
                "example": {
                    "detail": "User account is not activated.",
                },
            },
        },
    },
    500: {
        "description": "An unexpected dependency, database or response validation error occurred.",
    },
}


CHANGE_PASSWORD_RESPONSES = {
    200: {
        "description": "The password was changed. Log in again using the new password.",
        "content": {
            "application/json": {
                "example": {
                    "message": "Password changed successfully. Please log in again.",
                },
            },
        },
    },
    400: {
        "description": (
            "The old password is incorrect or the new password matches the current "
            "password."
        ),
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
            },
        },
    },
    401: moderator_error_responses[401],
    403: {
        "description": "The user account is not activated.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
                "example": {
                    "detail": "User account is not activated.",
                },
            },
        },
    },
    404: {
        "description": "The user no longer exists.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
            },
        },
    },
    422: {
        "description": (
            "Invalid or missing request fields. Values must satisfy the request "
            "schema, including email format and password validation where "
            "applicable."
        ),
    },
    500: {
        "description": "The password could not be changed.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
                "example": {
                    "detail": "An error occurred while changing the password.",
                },
            },
        },
    },
}


REQUEST_PASSWORD_RESET_RESPONSES = {
    200: {
        "description": (
            "The request was processed without revealing whether an active account "
            "exists or whether a new email was scheduled."
        ),
        "content": {
            "application/json": {
                "example": {
                    "message": (
                        "If the account exists and is active, the password reset "
                        "request has been processed."
                    ),
                },
            },
        },
    },
    422: {
        "description": (
            "Invalid or missing request fields. Values must satisfy the request "
            "schema, including email format and password validation where "
            "applicable."
        ),
    },
    500: {
        "description": "The password reset request could not be processed.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
                "example": {
                    "detail": "An error occurred while requesting a password reset.",
                },
            },
        },
    },
}


RESET_PASSWORD_RESPONSES = {
    200: {
        "description": "The password was reset and confirmation email sending was scheduled.",
        "content": {
            "application/json": {
                "example": {
                    "message": "Password reset successfully. Please log in.",
                },
            },
        },
    },
    400: {
        "description": (
            "The password reset token is invalid or expired, the email/token "
            "combination is not accepted, or the new password matches the current "
            "password."
        ),
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
            },
        },
    },
    422: {
        "description": (
            "Invalid or missing request fields. Values must satisfy the request "
            "schema, including email format and password validation where "
            "applicable."
        ),
    },
    500: {
        "description": "The password reset or confirmation email scheduling failed.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
                "example": {
                    "detail": "An error occurred while resetting the password.",
                },
            },
        },
    },
}


ADMIN_ACTIVATE_ACCOUNT_RESPONSES = {
    200: {
        "description": (
            "The administrator activated the account. This controller does not "
            "schedule an activation confirmation email."
        ),
        "content": {
            "application/json": {
                "example": {
                    "message": "User account activated successfully.",
                },
            },
        },
    },
    400: {
        "description": "The target account is already active.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
            },
        },
    },
    401: moderator_error_responses[401],
    403: {
        "description": (
            "The authenticated account is inactive or does not have administrator "
            "permissions."
        ),
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
            },
        },
    },
    404: {
        "description": "The target user does not exist.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
            },
        },
    },
    422: {
        "description": "User ID must be an integer greater than or equal to 1.",
    },
    500: {
        "description": "The account could not be activated.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
                "example": {
                    "detail": "An error occurred during account activation.",
                },
            },
        },
    },
}


ADMIN_CHANGE_GROUP_RESPONSES = {
    200: {
        "description": "The user group was updated successfully.",
        "content": {
            "application/json": {
                "example": {
                    "message": "User group updated successfully.",
                },
            },
        },
    },
    401: moderator_error_responses[401],
    403: {
        "description": (
            "The authenticated account is inactive or does not have administrator "
            "permissions."
        ),
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
            },
        },
    },
    404: {
        "description": "The target user does not exist.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
            },
        },
    },
    422: {
        "description": (
            "Invalid user ID or request body. User ID must be an integer greater "
            "than or equal to 1. The group must be user, moderator or admin."
        ),
    },
    500: {
        "description": (
            "The group could not be updated or the requested group is missing from "
            "the database."
        ),
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "detail",
                    ],
                },
                "example": {
                    "detail": "An error occurred while updating the user group.",
                },
            },
        },
    },
}
