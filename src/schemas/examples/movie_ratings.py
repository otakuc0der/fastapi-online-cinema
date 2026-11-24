from schemas.examples.security import moderator_error_responses

movie_rating_request_example = {
    "rating": 8,
}

movie_rating_response_example = {
    "movie_id": 17,
    "rating": 8,
}

movie_rating_updated_response_example = {
    "movie_id": 17,
    "rating": 10,
}

movie_rating_absent_response_example = {
    "movie_id": 17,
    "rating": None,
}

movie_rating_summary_example = {
    "movie_id": 17,
    "average_rating": 8.5,
    "ratings_count": 2,
}

movie_rating_empty_summary_example = {
    "movie_id": 17,
    "average_rating": None,
    "ratings_count": 0,
}


MOVIE_RATING_AUTH_RESPONSES = {
    401: moderator_error_responses[401],
    403: {
        "description": (
            "The user account is inactive. Any active user can manage "
            "their own movie ratings, regardless of role."
        ),
        "content": {
            "application/json": {
                "example": {
                    "detail": "User account is not activated.",
                },
            },
        },
    },
}


MOVIE_RATING_NOT_FOUND_RESPONSE = {
    "description": "The movie does not exist.",
    "content": {
        "application/json": {
            "example": {
                "detail": "Movie not found.",
            },
        },
    },
}


MOVIE_RATING_MUTATION_NOT_FOUND_RESPONSE = {
    **MOVIE_RATING_NOT_FOUND_RESPONSE,
    "description": (
        "The movie does not exist, or the authenticated user "
        "no longer exists when the operation is performed."
    ),
}


MOVIE_RATING_PATH_VALIDATION_RESPONSE = {
    "description": "Movie ID must be an integer greater than zero.",
}


SET_MOVIE_RATING_RESPONSES = {
    **MOVIE_RATING_AUTH_RESPONSES,
    200: {
        "description": (
            "The user's rating was created or updated. "
            "Repeated requests do not create duplicate records."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "rating_saved": {
                        "summary": "Rating saved",
                        "value": movie_rating_response_example,
                    },
                    "rating_updated": {
                        "summary": "Existing rating changed to 10",
                        "value": movie_rating_updated_response_example,
                    },
                },
            },
        },
    },
    404: MOVIE_RATING_MUTATION_NOT_FOUND_RESPONSE,
    422: {
        "description": (
            "Invalid movie ID or request body. Rating is required and must "
            "be a JSON integer from 1 to 10. Strings, floating-point numbers, "
            "booleans and null are rejected. Unknown fields are rejected."
        ),
    },
    500: {
        "description": "The movie rating could not be saved.",
        "content": {
            "application/json": {
                "example": {
                    "detail": ("An error occurred while setting the movie rating."),
                },
            },
        },
    },
}


DELETE_MOVIE_RATING_RESPONSES = {
    **MOVIE_RATING_AUTH_RESPONSES,
    204: {
        "description": (
            "The user's rating is absent. Repeated deletion also succeeds. "
            "No response body."
        ),
    },
    404: MOVIE_RATING_MUTATION_NOT_FOUND_RESPONSE,
    422: MOVIE_RATING_PATH_VALIDATION_RESPONSE,
    500: {
        "description": "The movie rating could not be deleted.",
        "content": {
            "application/json": {
                "example": {
                    "detail": ("An error occurred while deleting the movie rating."),
                },
            },
        },
    },
}


GET_CURRENT_MOVIE_RATING_RESPONSES = {
    **MOVIE_RATING_AUTH_RESPONSES,
    200: {
        "description": (
            "The current user's rating, or null if the movie "
            "has not been rated by this user."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "rated": {
                        "summary": "The user has rated the movie",
                        "value": movie_rating_response_example,
                    },
                    "not_rated": {
                        "summary": "The user has not rated the movie",
                        "value": movie_rating_absent_response_example,
                    },
                },
            },
        },
    },
    404: MOVIE_RATING_NOT_FOUND_RESPONSE,
    422: MOVIE_RATING_PATH_VALIDATION_RESPONSE,
    500: {
        "description": "The current user's rating could not be retrieved.",
        "content": {
            "application/json": {
                "example": {
                    "detail": ("An error occurred while retrieving the movie rating."),
                },
            },
        },
    },
}


GET_MOVIE_RATING_SUMMARY_RESPONSES = {
    200: {
        "description": (
            "The average user rating and number of ratings. "
            "Without ratings, the average is null and the count is zero."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "with_ratings": {
                        "summary": "The movie has user ratings",
                        "value": movie_rating_summary_example,
                    },
                    "without_ratings": {
                        "summary": "The movie has no user ratings",
                        "value": movie_rating_empty_summary_example,
                    },
                },
            },
        },
    },
    404: MOVIE_RATING_NOT_FOUND_RESPONSE,
    422: MOVIE_RATING_PATH_VALIDATION_RESPONSE,
    500: {
        "description": "The movie rating summary could not be retrieved.",
        "content": {
            "application/json": {
                "example": {
                    "detail": (
                        "An error occurred while retrieving "
                        "the movie rating summary."
                    ),
                },
            },
        },
    },
}
