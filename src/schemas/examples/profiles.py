PROFILE_EXAMPLE = {
    "id": 1,
    "user_id": 17,
    "first_name": "anna",
    "last_name": "smith",
    "gender": "woman",
    "date_of_birth": "2000-05-15",
    "info": "I enjoy science fiction and classic movies.",
    "avatar": "http://localhost:9000/cinema-storage/avatars/17-avatar-0123456789abcdef0123456789abcdef.jpg",
}


PROFILE_WITHOUT_AVATAR_EXAMPLE = {
    "id": 1,
    "user_id": 17,
    "first_name": "anna",
    "last_name": "smith",
    "gender": "woman",
    "date_of_birth": "2000-05-15",
    "info": "I enjoy science fiction and classic movies.",
    "avatar": None,
}


VALIDATION_ERROR_SCHEMA = {
    "type": "object",
    "properties": {
        "detail": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "loc": {
                        "type": "array",
                        "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
                    },
                    "msg": {"type": "string"},
                    "type": {"type": "string"},
                },
                "required": ["loc", "msg", "type"],
            },
        }
    },
    "required": ["detail"],
}


COMMON_PROFILE_ERROR_RESPONSES = {
    401: {
        "description": "Authentication is required. The access token is missing, invalid or expired."
    },
    403: {
        "description": (
            "Access is restricted to the profile owner and administrators. An "
            "inactive authenticated account may also be rejected."
        ),
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                    "required": ["detail"],
                },
                "example": {
                    "detail": "You don't have permission to access this profile."
                },
            }
        },
    },
}


PROFILE_UPDATE_EXAMPLES = {
    "update_info": {
        "summary": "Change only the biography",
        "value": {"info": "I enjoy documentaries and independent cinema."},
    },
    "update_names": {
        "summary": "Change first and last names",
        "value": {"first_name": "Anna", "last_name": "Smith"},
    },
    "empty_update": {"summary": "Leave all fields unchanged", "value": {}},
}


GET_PROFILE_RESPONSES = {
    **COMMON_PROFILE_ERROR_RESPONSES,
    422: {
        "description": "The user ID is invalid.",
        "content": {
            "application/json": {
                "schema": VALIDATION_ERROR_SCHEMA,
                "examples": {
                    "invalid_user_id": {
                        "summary": "User ID must be positive",
                        "value": {
                            "detail": [
                                {
                                    "type": "greater_than_equal",
                                    "loc": ["path", "user_id"],
                                    "msg": "Input should be greater than or equal to 1",
                                    "input": 0,
                                    "ctx": {"ge": 1},
                                }
                            ]
                        },
                    }
                },
            }
        },
    },
    200: {
        "description": "The profile was retrieved successfully.",
        "content": {
            "application/json": {
                "examples": {
                    "with_avatar": {
                        "summary": "Profile with an avatar",
                        "value": PROFILE_EXAMPLE,
                    },
                    "without_avatar": {
                        "summary": "Profile without an avatar",
                        "value": PROFILE_WITHOUT_AVATAR_EXAMPLE,
                    },
                }
            }
        },
    },
    404: {
        "description": "The profile does not exist. For modifying operations, the target user may also be missing.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                    "required": ["detail"],
                },
                "example": {"detail": "User profile not found."},
            }
        },
    },
    500: {
        "description": "An unexpected error occurred while retrieving the profile or checking permissions.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                    "required": ["detail"],
                },
                "example": {
                    "detail": "An error occurred while retrieving the profile."
                },
            }
        },
    },
}


CREATE_PROFILE_RESPONSES = {
    **COMMON_PROFILE_ERROR_RESPONSES,
    422: {
        "description": (
            "Invalid form fields or user ID. Names must contain only English "
            "letters (at most 100 characters), biography must not be blank, and the "
            "birth date must be in 1900 or later and represent an age of at least "
            "18. An optional avatar must be a non-empty valid JPEG or PNG image no "
            "larger than 1 MiB (1,048,576 bytes)."
        ),
        "content": {
            "application/json": {
                "schema": VALIDATION_ERROR_SCHEMA,
                "examples": {
                    "invalid_name": {
                        "summary": "Invalid name",
                        "value": {
                            "detail": [
                                {
                                    "type": "value_error",
                                    "loc": ["body", "first_name"],
                                    "msg": "Value error, Name must contain only English letters and cannot be empty.",
                                }
                            ]
                        },
                    },
                    "avatar_too_large": {
                        "summary": "Avatar exceeds 1 MiB",
                        "value": {
                            "detail": [
                                {
                                    "type": "value_error",
                                    "loc": ["body", "avatar"],
                                    "msg": "Value error, Avatar size must not exceed 1 MiB.",
                                }
                            ]
                        },
                    },
                },
            }
        },
    },
    201: {
        "description": "A profile was created successfully.",
        "content": {
            "application/json": {
                "examples": {
                    "with_avatar": {
                        "summary": "Profile with an avatar",
                        "value": PROFILE_EXAMPLE,
                    },
                    "without_avatar": {
                        "summary": "Profile without an avatar",
                        "value": PROFILE_WITHOUT_AVATAR_EXAMPLE,
                    },
                }
            }
        },
    },
    404: {"description": "The target user does not exist."},
    409: {
        "description": "The user already has a profile.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                    "required": ["detail"],
                },
                "example": {"detail": "User already has a profile."},
            }
        },
    },
    500: {
        "description": "Profile creation failed, for example because the database or avatar storage is unavailable.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                    "required": ["detail"],
                },
                "example": {"detail": "An error occurred while creating the profile."},
            }
        },
    },
}


UPDATE_PROFILE_RESPONSES = {
    **COMMON_PROFILE_ERROR_RESPONSES,
    422: {
        "description": (
            "Invalid user ID, invalid field values, explicit null values or unknown "
            "fields. An empty JSON object is allowed."
        ),
        "content": {
            "application/json": {
                "schema": VALIDATION_ERROR_SCHEMA,
                "examples": {
                    "null_info": {
                        "summary": "Explicit null is rejected",
                        "value": {
                            "detail": [
                                {
                                    "type": "value_error",
                                    "loc": ["body", "info"],
                                    "msg": "Value error, Info cannot be null.",
                                }
                            ]
                        },
                    },
                    "unknown_field": {
                        "summary": "Unknown field is rejected",
                        "value": {
                            "detail": [
                                {
                                    "type": "extra_forbidden",
                                    "loc": ["body", "nickname"],
                                    "msg": "Extra inputs are not permitted",
                                    "input": "movie_fan",
                                }
                            ]
                        },
                    },
                },
            }
        },
    },
    200: {
        "description": "The supplied fields were updated. Omitted fields remain unchanged.",
        "content": {
            "application/json": {
                "examples": {
                    "updated": {
                        "summary": "Updated profile",
                        "value": {
                            "id": 1,
                            "user_id": 17,
                            "first_name": "anna",
                            "last_name": "smith",
                            "gender": "woman",
                            "date_of_birth": "2000-05-15",
                            "info": "I enjoy documentaries and independent cinema.",
                            "avatar": (
                                "http://localhost:9000/cinema-storage/avatars/"
                                "17-avatar-0123456789abcdef0123456789abcdef.jpg"
                            ),
                        },
                    }
                }
            }
        },
    },
    404: {
        "description": "The profile does not exist. For modifying operations, the target user may also be missing.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                    "required": ["detail"],
                },
                "example": {"detail": "User profile not found."},
            }
        },
    },
    500: {
        "description": "An unexpected error occurred while updating the profile or checking permissions.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                    "required": ["detail"],
                },
                "example": {"detail": "An error occurred while updating the profile."},
            }
        },
    },
}


UPDATE_AVATAR_RESPONSES = {
    **COMMON_PROFILE_ERROR_RESPONSES,
    422: {
        "description": (
            "Invalid user ID, missing avatar, or invalid image. The file must be a "
            "non-empty valid JPEG or PNG image no larger than 1 MiB (1,048,576 "
            "bytes)."
        ),
        "content": {
            "application/json": {
                "schema": VALIDATION_ERROR_SCHEMA,
                "examples": {
                    "missing_avatar": {
                        "summary": "A file is required",
                        "value": {
                            "detail": [
                                {
                                    "type": "missing",
                                    "loc": ["body", "avatar"],
                                    "msg": "Field required",
                                    "input": None,
                                }
                            ]
                        },
                    },
                    "invalid_image": {
                        "summary": "Invalid or corrupted image",
                        "value": {
                            "detail": [
                                {
                                    "type": "value_error",
                                    "loc": ["body", "avatar"],
                                    "msg": "Value error, Avatar must be a valid, non-corrupted JPEG or PNG image.",
                                }
                            ]
                        },
                    },
                },
            }
        },
    },
    200: {
        "description": "The avatar was uploaded or replaced. The complete updated profile is returned.",
        "content": {
            "application/json": {
                "examples": {
                    "updated": {
                        "summary": "Profile with the new avatar",
                        "value": PROFILE_EXAMPLE,
                    }
                }
            }
        },
    },
    404: {
        "description": "The profile does not exist. For modifying operations, the target user may also be missing.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                    "required": ["detail"],
                },
                "example": {"detail": "User profile not found."},
            }
        },
    },
    500: {
        "description": "The avatar update failed, for example because the database or storage is unavailable.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                    "required": ["detail"],
                },
                "example": {
                    "detail": "An error occurred while updating the profile avatar."
                },
            }
        },
    },
}


DELETE_AVATAR_RESPONSES = {
    **COMMON_PROFILE_ERROR_RESPONSES,
    422: {
        "description": "The user ID is invalid.",
        "content": {
            "application/json": {
                "schema": VALIDATION_ERROR_SCHEMA,
                "examples": {
                    "invalid_user_id": {
                        "summary": "User ID must be positive",
                        "value": {
                            "detail": [
                                {
                                    "type": "greater_than_equal",
                                    "loc": ["path", "user_id"],
                                    "msg": "Input should be greater than or equal to 1",
                                    "input": 0,
                                    "ctx": {"ge": 1},
                                }
                            ]
                        },
                    }
                },
            }
        },
    },
    200: {
        "description": (
            "The avatar reference was cleared. A profile without an avatar is "
            "returned. Repeated removal also succeeds."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "without_avatar": {
                        "summary": "Profile after avatar removal",
                        "value": PROFILE_WITHOUT_AVATAR_EXAMPLE,
                    }
                }
            }
        },
    },
    404: {
        "description": "The profile does not exist. For modifying operations, the target user may also be missing.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                    "required": ["detail"],
                },
                "example": {"detail": "User profile not found."},
            }
        },
    },
    500: {
        "description": "An unexpected error occurred while clearing the avatar reference or checking permissions.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                    "required": ["detail"],
                },
                "example": {
                    "detail": "An error occurred while deleting the profile avatar."
                },
            }
        },
    },
}


DELETE_PROFILE_RESPONSES = {
    **COMMON_PROFILE_ERROR_RESPONSES,
    422: {
        "description": "The user ID is invalid.",
        "content": {
            "application/json": {
                "schema": VALIDATION_ERROR_SCHEMA,
                "examples": {
                    "invalid_user_id": {
                        "summary": "User ID must be positive",
                        "value": {
                            "detail": [
                                {
                                    "type": "greater_than_equal",
                                    "loc": ["path", "user_id"],
                                    "msg": "Input should be greater than or equal to 1",
                                    "input": 0,
                                    "ctx": {"ge": 1},
                                }
                            ]
                        },
                    }
                },
            }
        },
    },
    204: {
        "description": "The profile was deleted. The user account remains. This response has no body."
    },
    404: {
        "description": "The profile does not exist. For modifying operations, the target user may also be missing.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                    "required": ["detail"],
                },
                "example": {"detail": "User profile not found."},
            }
        },
    },
    500: {
        "description": "An unexpected error occurred while deleting the profile or checking permissions.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                    "required": ["detail"],
                },
                "example": {"detail": "An error occurred while deleting the profile."},
            }
        },
    },
}
