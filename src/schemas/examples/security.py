moderator_error_responses = {
    401: {
        "description": (
            "Bearer authentication is required. The access token is missing, "
            "invalid or expired, or its user no longer exists."
        ),
        "headers": {
            "WWW-Authenticate": {
                "description": "Required authentication scheme.",
                "schema": {"type": "string"},
                "example": "Bearer",
            },
        },
        "content": {
            "application/json": {
                "examples": {
                    "missing_header": {
                        "summary": "Authorization header is missing",
                        "value": {"detail": "Authorization header is missing"},
                    },
                    "invalid_header": {
                        "summary": "Authorization header has an invalid format",
                        "value": {
                            "detail": (
                                "Invalid Authorization header format. "
                                "Expected 'Bearer <token>'"
                            ),
                        },
                    },
                    "invalid_token": {
                        "summary": "Access token is invalid",
                        "value": {"detail": "Invalid access token."},
                    },
                    "expired_token": {
                        "summary": "Access token has expired",
                        "value": {"detail": "Access token has expired."},
                    },
                },
            },
        },
    },
    403: {
        "description": (
            "The account is inactive or the user does not have moderator "
            "or administrator permissions."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "insufficient_permissions": {
                        "summary": "Moderator or administrator role is required",
                        "value": {
                            "detail": (
                                "Moderator or administrator permissions "
                                "are required."
                            ),
                        },
                    },
                    "inactive_account": {
                        "summary": "User account is inactive",
                        "value": {"detail": "User account is not activated."},
                    },
                },
            },
        },
    },
}
