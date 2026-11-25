from fastapi.openapi.models import Example

from schemas.examples.security import moderator_error_responses

movie_comment_create_example = {
    "text": "Great performances and a memorable ending.",
}

movie_comment_update_example = {
    "text": "Great performances, a memorable ending and an excellent soundtrack.",
}

movie_comment_response_example = {
    "id": 42,
    "user_id": 17,
    "movie_id": 1000,
    "text": movie_comment_create_example["text"],
    "created_at": "2026-11-25T12:00:00Z",
    "updated_at": "2026-11-25T12:00:00Z",
}

movie_comment_updated_response_example = {
    **movie_comment_response_example,
    "text": movie_comment_update_example["text"],
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
        value=movie_comment_create_example,
    ),
}

MOVIE_COMMENT_UPDATE_REQUEST_EXAMPLES: dict[str, Example] = {
    "comment": Example(
        summary="Replace the comment text",
        value=movie_comment_update_example,
    ),
}


MOVIE_COMMENT_AUTH_RESPONSES = {
    401: moderator_error_responses[401],
    403: {
        "description": "The user account is inactive.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "User account is not activated.",
                },
            },
        },
    },
}


MOVIE_COMMENT_AUTHOR_ERROR_RESPONSE = {
    "description": (
        "The user account is inactive or the comment belongs to another user. "
        "Moderator and administrator roles do not bypass author checks."
    ),
    "content": {
        "application/json": {
            "examples": {
                "inactive_account": {
                    "summary": "The account is inactive",
                    "value": {
                        "detail": "User account is not activated.",
                    },
                },
                "not_author": {
                    "summary": "The user is not the comment author",
                    "value": {
                        "detail": ("You don't have permission to modify this comment."),
                    },
                },
            },
        },
    },
}


MOVIE_COMMENT_MOVIE_NOT_FOUND_RESPONSE = {
    "description": "The movie does not exist.",
    "content": {
        "application/json": {
            "example": {
                "detail": "Movie not found.",
            },
        },
    },
}


MOVIE_COMMENT_NOT_FOUND_RESPONSE = {
    "description": (
        "The movie or comment does not exist. A comment belonging "
        "to another movie is also treated as not found."
    ),
    "content": {
        "application/json": {
            "examples": {
                "movie_not_found": {
                    "summary": "The movie does not exist",
                    "value": {
                        "detail": "Movie not found.",
                    },
                },
                "comment_not_found": {
                    "summary": "The comment does not exist in this movie",
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
        "The movie or comment does not exist, the comment belongs "
        "to another movie, or the authenticated user no longer exists "
        "when the operation is performed."
    ),
}


MOVIE_COMMENT_BODY_VALIDATION_RESPONSE = {
    "description": (
        "Invalid path parameters or request body. IDs must be integers "
        "greater than zero. Text is required and must be a string containing "
        "1–2000 characters after trimming surrounding whitespace. "
        "Empty text, whitespace-only text, null and unknown fields are rejected."
    ),
}


MOVIE_COMMENT_PATH_VALIDATION_RESPONSE = {
    "description": ("Movie ID and comment ID must be integers greater than zero."),
}


LIST_MOVIE_COMMENTS_RESPONSES = {
    200: {
        "description": (
            "A page of comments ordered from newest to oldest. "
            "The first page may contain an empty list."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "comments": {
                        "summary": "Comments with pagination",
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
            "The movie does not exist, or a page greater than 1 "
            "contains no comments."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "movie_not_found": {
                        "summary": "The movie does not exist",
                        "value": {
                            "detail": "Movie not found.",
                        },
                    },
                    "empty_page": {
                        "summary": "The requested page has no comments",
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
            "Movie ID and page must be integers greater than zero. "
            "Per_page must be an integer from 1 to 20."
        ),
    },
    500: {
        "description": "Movie comments could not be retrieved.",
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
        "description": "The requested movie comment.",
        "content": {
            "application/json": {
                "example": movie_comment_response_example,
            },
        },
    },
    404: MOVIE_COMMENT_NOT_FOUND_RESPONSE,
    422: MOVIE_COMMENT_PATH_VALIDATION_RESPONSE,
    500: {
        "description": "The movie comment could not be retrieved.",
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
        "description": "A new movie comment was created.",
        "content": {
            "application/json": {
                "example": movie_comment_response_example,
            },
        },
    },
    404: {
        **MOVIE_COMMENT_MOVIE_NOT_FOUND_RESPONSE,
        "description": (
            "The movie does not exist, or the authenticated user "
            "no longer exists when the operation is performed."
        ),
    },
    422: MOVIE_COMMENT_BODY_VALIDATION_RESPONSE,
    500: {
        "description": "The movie comment could not be created.",
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
        "description": "The comment with its updated text and timestamps.",
        "content": {
            "application/json": {
                "example": movie_comment_updated_response_example,
            },
        },
    },
    403: MOVIE_COMMENT_AUTHOR_ERROR_RESPONSE,
    404: MOVIE_COMMENT_MUTATION_NOT_FOUND_RESPONSE,
    422: MOVIE_COMMENT_BODY_VALIDATION_RESPONSE,
    500: {
        "description": "The movie comment could not be updated.",
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
        "description": "The comment was deleted. No response body.",
    },
    403: MOVIE_COMMENT_AUTHOR_ERROR_RESPONSE,
    404: MOVIE_COMMENT_MUTATION_NOT_FOUND_RESPONSE,
    422: MOVIE_COMMENT_PATH_VALIDATION_RESPONSE,
    500: {
        "description": "The movie comment could not be deleted.",
        "content": {
            "application/json": {
                "example": {
                    "detail": ("An error occurred while deleting the movie comment."),
                },
            },
        },
    },
}
