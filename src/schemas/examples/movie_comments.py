from fastapi.openapi.models import Example

movie_comment_create_request_example = {
    "text": "Great performances and a memorable ending.",
}

movie_comment_update_request_example = {
    "text": "Great performances and an excellent soundtrack.",
}

movie_comment_response_example = {
    "id": 42,
    "user_id": 17,
    "movie_id": 1000,
    "text": "Great performances and a memorable ending.",
    "created_at": "2026-11-25T12:00:00Z",
    "updated_at": "2026-11-25T12:00:00Z",
}

movie_comment_updated_response_example = {
    **movie_comment_response_example,
    "text": "Great performances and an excellent soundtrack.",
    "updated_at": "2026-11-25T12:05:00Z",
}

movie_comment_list_response_example = {
    "comments": [movie_comment_response_example],
    "prev_page": None,
    "next_page": "/api/v1/movies/1000/comments/?page=2&per_page=1",
    "total_pages": 3,
    "total_items": 3,
}

movie_comment_empty_list_response_example = {
    "comments": [],
    "prev_page": None,
    "next_page": None,
    "total_pages": 0,
    "total_items": 0,
}


MOVIE_COMMENT_CREATE_REQUEST_EXAMPLES: dict[str, Example] = {
    "comment": Example(
        summary="Create a movie comment",
        value=movie_comment_create_request_example,
    ),
}

MOVIE_COMMENT_UPDATE_REQUEST_EXAMPLES: dict[str, Example] = {
    "comment": Example(
        summary="Update the comment text",
        value=movie_comment_update_request_example,
    ),
}


MOVIE_COMMENT_AUTH_RESPONSES = {
    401: {
        "description": (
            "Authentication is required. The Bearer access token is missing, "
            "invalid or expired, or its user no longer exists."
        ),
    },
}

MOVIE_COMMENT_INACTIVE_USER_RESPONSE = {
    "description": "The authenticated user's account is not active.",
}

MOVIE_COMMENT_UPDATE_PERMISSION_RESPONSE = {
    "description": (
        "The authenticated user's account is not active, or the user is not "
        "the comment author. Moderators and administrators cannot edit "
        "other users' comments."
    ),
    "content": {
        "application/json": {
            "examples": {
                "permission_denied": {
                    "summary": "Only the author can edit the comment",
                    "value": {
                        "detail": ("You don't have permission to modify this comment."),
                    },
                },
            },
        },
    },
}

MOVIE_COMMENT_DELETE_PERMISSION_RESPONSE = {
    "description": (
        "The authenticated user's account is not active, or the user is "
        "neither the comment author nor an administrator. Moderators cannot "
        "delete other users' comments."
    ),
    "content": {
        "application/json": {
            "examples": {
                "permission_denied": {
                    "summary": (
                        "Only the author or an administrator can delete " "the comment"
                    ),
                    "value": {
                        "detail": ("You don't have permission to modify this comment."),
                    },
                },
            },
        },
    },
}

MOVIE_COMMENT_NOT_FOUND_RESPONSE = {
    "description": (
        "The movie does not exist, the comment does not exist, "
        "or the comment belongs to another movie."
    ),
    "content": {
        "application/json": {
            "examples": {
                "movie_not_found": {
                    "summary": "Movie not found",
                    "value": {
                        "detail": "Movie not found.",
                    },
                },
                "comment_not_found": {
                    "summary": ("Comment not found or belongs to another movie"),
                    "value": {
                        "detail": "Movie comment not found.",
                    },
                },
            },
        },
    },
}

MOVIE_COMMENT_MUTATION_NOT_FOUND_RESPONSE = {
    **MOVIE_COMMENT_NOT_FOUND_RESPONSE,
    "description": (
        "The movie does not exist, the comment does not exist, "
        "the comment belongs to another movie, or the authenticated "
        "user was removed before the operation completed."
    ),
}

MOVIE_COMMENT_BODY_VALIDATION_RESPONSE = {
    "description": (
        "Validation failed. Path IDs must be positive integers. "
        "The request body must contain a text string with 1–2000 characters "
        "after trimming surrounding whitespace. Missing text, null, "
        "blank text and additional request fields are rejected."
    ),
}

MOVIE_COMMENT_PATH_VALIDATION_RESPONSE = {
    "description": (
        "Validation failed. Movie ID and comment ID must be " "positive integers."
    ),
}


LIST_MOVIE_COMMENTS_RESPONSES = {
    200: {
        "description": (
            "Comment page with matching totals and relative navigation links. "
            "An existing movie with no comments returns an empty first page."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "comment_page": {
                        "summary": "First page with more comments available",
                        "value": movie_comment_list_response_example,
                    },
                    "empty_first_page": {
                        "summary": "The movie has no comments",
                        "value": movie_comment_empty_list_response_example,
                    },
                },
            },
        },
    },
    404: {
        "description": (
            "The movie does not exist, or the requested page is empty "
            "and its number is greater than 1."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "movie_not_found": {
                        "summary": "Movie not found",
                        "value": {
                            "detail": "Movie not found.",
                        },
                    },
                    "empty_page": {
                        "summary": "Empty page after the first page",
                        "value": {
                            "detail": ("No comments found on the requested page."),
                        },
                    },
                },
            },
        },
    },
    422: {
        "description": (
            "Validation failed. Movie ID and page must be positive integers. "
            "Per_page must be an integer from 1 to 20."
        ),
    },
    500: {
        "description": "An unexpected error prevented retrieving comments.",
        "content": {
            "application/json": {
                "example": {
                    "detail": ("An error occurred while retrieving movie comments."),
                },
            },
        },
    },
}

GET_MOVIE_COMMENT_RESPONSES = {
    200: {
        "description": "Comment text, author ID, movie ID and timestamps.",
        "content": {
            "application/json": {
                "example": movie_comment_response_example,
            },
        },
    },
    404: MOVIE_COMMENT_NOT_FOUND_RESPONSE,
    422: MOVIE_COMMENT_PATH_VALIDATION_RESPONSE,
    500: {
        "description": "An unexpected error prevented retrieving the comment.",
        "content": {
            "application/json": {
                "example": {
                    "detail": ("An error occurred while retrieving the movie comment."),
                },
            },
        },
    },
}

CREATE_MOVIE_COMMENT_RESPONSES = {
    **MOVIE_COMMENT_AUTH_RESPONSES,
    201: {
        "description": "Created comment with generated ID and timestamps.",
        "content": {
            "application/json": {
                "example": movie_comment_response_example,
            },
        },
    },
    403: MOVIE_COMMENT_INACTIVE_USER_RESPONSE,
    404: {
        "description": (
            "The movie does not exist, or the authenticated user was "
            "removed before the operation completed."
        ),
        "content": {
            "application/json": {
                "example": {
                    "detail": "Movie not found.",
                },
            },
        },
    },
    422: MOVIE_COMMENT_BODY_VALIDATION_RESPONSE,
    500: {
        "description": "An unexpected error prevented creating the comment.",
        "content": {
            "application/json": {
                "example": {
                    "detail": ("An error occurred while creating the movie comment."),
                },
            },
        },
    },
}

UPDATE_MOVIE_COMMENT_RESPONSES = {
    **MOVIE_COMMENT_AUTH_RESPONSES,
    200: {
        "description": "Comment with the updated text and timestamps.",
        "content": {
            "application/json": {
                "example": movie_comment_updated_response_example,
            },
        },
    },
    403: MOVIE_COMMENT_UPDATE_PERMISSION_RESPONSE,
    404: MOVIE_COMMENT_MUTATION_NOT_FOUND_RESPONSE,
    422: MOVIE_COMMENT_BODY_VALIDATION_RESPONSE,
    500: {
        "description": "An unexpected error prevented updating the comment.",
        "content": {
            "application/json": {
                "example": {
                    "detail": ("An error occurred while updating the movie comment."),
                },
            },
        },
    },
}

DELETE_MOVIE_COMMENT_RESPONSES = {
    **MOVIE_COMMENT_AUTH_RESPONSES,
    204: {
        "description": "Comment deleted successfully. No response body.",
    },
    403: MOVIE_COMMENT_DELETE_PERMISSION_RESPONSE,
    404: MOVIE_COMMENT_MUTATION_NOT_FOUND_RESPONSE,
    422: MOVIE_COMMENT_PATH_VALIDATION_RESPONSE,
    500: {
        "description": "An unexpected error prevented deleting the comment.",
        "content": {
            "application/json": {
                "example": {
                    "detail": ("An error occurred while deleting the movie comment."),
                },
            },
        },
    },
}
