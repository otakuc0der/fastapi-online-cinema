from schemas.examples.security import moderator_error_responses

movie_like_request_example = {"reaction": "like"}
movie_dislike_request_example = {"reaction": "dislike"}

movie_like_response_example = {"movie_id": 17, "reaction": "like"}
movie_dislike_response_example = {"movie_id": 17, "reaction": "dislike"}
movie_no_reaction_response_example = {"movie_id": 17, "reaction": None}

movie_reaction_summary_example = {"movie_id": 17, "likes": 5, "dislikes": 2}
movie_reaction_empty_summary_example = {"movie_id": 17, "likes": 0, "dislikes": 0}

MOVIE_REACTION_REQUEST_EXAMPLES = {
    "like": {
        "summary": "Set a like",
        "description": "Create a like or replace the current dislike with a like.",
        "value": movie_like_request_example,
    },
    "dislike": {
        "summary": "Set a dislike",
        "description": "Create a dislike or replace the current like with a dislike.",
        "value": movie_dislike_request_example,
    },
}

MOVIE_REACTION_AUTH_RESPONSES = {
    401: moderator_error_responses[401],
    403: {
        "description": (
            "The authenticated account is inactive. "
            "No moderator or administrator role is required."
        ),
        "content": {
            "application/json": {
                "example": {"detail": "User account is not activated."},
            },
        },
    },
}

MOVIE_REACTION_NOT_FOUND_RESPONSE = {
    "description": "The requested movie does not exist.",
    "content": {
        "application/json": {
            "example": {"detail": "Movie not found."},
        },
    },
}

MOVIE_REACTION_MUTATION_NOT_FOUND_RESPONSE = {
    **MOVIE_REACTION_NOT_FOUND_RESPONSE,
    "description": (
        "The requested movie does not exist, or the authenticated user "
        "was no longer found when the service checked the account."
    ),
}

MOVIE_REACTION_PATH_VALIDATION_RESPONSE = {
    "description": "Movie ID must be an integer greater than or equal to 1.",
}

SET_MOVIE_REACTION_RESPONSES = {
    **MOVIE_REACTION_AUTH_RESPONSES,
    200: {
        "description": (
            "The reaction was created or updated. Repeating the same reaction "
            "also succeeds without creating another record."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "like": {
                        "summary": "The current user likes the movie",
                        "value": movie_like_response_example,
                    },
                    "dislike": {
                        "summary": "The current user dislikes the movie",
                        "value": movie_dislike_response_example,
                    },
                },
            },
        },
    },
    404: MOVIE_REACTION_MUTATION_NOT_FOUND_RESPONSE,
    422: {
        "description": (
            "Invalid movie ID or JSON body. The reaction field is required "
            "and accepts only 'like' or 'dislike'. Null values and unknown "
            "request fields are rejected. Movie ID must be at least 1."
        ),
    },
    500: {
        "description": "The reaction could not be saved or its response prepared.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An error occurred while setting the movie reaction.",
                },
            },
        },
    },
}

DELETE_MOVIE_REACTION_RESPONSES = {
    **MOVIE_REACTION_AUTH_RESPONSES,
    204: {
        "description": (
            "The current user's reaction was removed, or no reaction existed. "
            "The response has no body. Other users' reactions are unchanged."
        ),
    },
    404: MOVIE_REACTION_MUTATION_NOT_FOUND_RESPONSE,
    422: MOVIE_REACTION_PATH_VALIDATION_RESPONSE,
    500: {
        "description": "The reaction could not be deleted.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An error occurred while deleting the movie reaction.",
                },
            },
        },
    },
}

GET_MOVIE_REACTION_SUMMARY_RESPONSES = {
    200: {
        "description": (
            "The total numbers of likes and dislikes for the movie. "
            "Both counts are zero when an existing movie has no reactions."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "with_reactions": {
                        "summary": "Movie with reactions",
                        "value": movie_reaction_summary_example,
                    },
                    "without_reactions": {
                        "summary": "Movie without reactions",
                        "value": movie_reaction_empty_summary_example,
                    },
                },
            },
        },
    },
    404: MOVIE_REACTION_NOT_FOUND_RESPONSE,
    422: MOVIE_REACTION_PATH_VALIDATION_RESPONSE,
    500: {
        "description": "The movie reaction counts could not be retrieved.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An error occurred while retrieving movie reactions.",
                },
            },
        },
    },
}

GET_CURRENT_MOVIE_REACTION_RESPONSES = {
    **MOVIE_REACTION_AUTH_RESPONSES,
    200: {
        "description": (
            "The current user's reaction to the movie. "
            "A missing reaction is represented by null, not a 404 response."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "like": {
                        "summary": "The current user likes the movie",
                        "value": movie_like_response_example,
                    },
                    "dislike": {
                        "summary": "The current user dislikes the movie",
                        "value": movie_dislike_response_example,
                    },
                    "no_reaction": {
                        "summary": "The current user has no reaction",
                        "value": movie_no_reaction_response_example,
                    },
                },
            },
        },
    },
    404: MOVIE_REACTION_NOT_FOUND_RESPONSE,
    422: MOVIE_REACTION_PATH_VALIDATION_RESPONSE,
    500: {
        "description": "The current user's movie reaction could not be retrieved.",
        "content": {
            "application/json": {
                "example": {
                    "detail": (
                        "An error occurred while retrieving the movie reaction."
                    ),
                },
            },
        },
    },
}
