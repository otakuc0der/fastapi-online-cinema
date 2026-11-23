from schemas.examples.movies import movie_list_item_example
from schemas.examples.security import moderator_error_responses

movie_favorite_response_example = {
    "user_id": 17,
    "movie_id": 1000,
}

movie_favorite_list_response_example = {
    "movies": [movie_list_item_example],
    "prev_page": None,
    "next_page": "/api/v1/movies/favorites/?per_page=1&page=2",
    "total_pages": 3,
    "total_items": 3,
}

movie_favorite_filtered_list_response_example = {
    "movies": [movie_list_item_example],
    "prev_page": None,
    "next_page": (
        "/api/v1/movies/favorites/?per_page=1&page=2"
        "&year=2010&imdb_min=8.0&ordering=-imdb&search=dream"
    ),
    "total_pages": 2,
    "total_items": 2,
}


MOVIE_FAVORITE_AUTH_RESPONSES = {
    401: moderator_error_responses[401],
    403: {
        "description": (
            "The user account is inactive. "
            "Any active user can manage their own favorites, regardless of role."
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


MOVIE_FAVORITE_NOT_FOUND_RESPONSE = {
    "description": (
        "The movie does not exist, or the authenticated user "
        "no longer exists when the operation is performed."
    ),
    "content": {
        "application/json": {
            "example": {
                "detail": "Movie not found.",
            },
        },
    },
}


LIST_FAVORITE_MOVIES_RESPONSES = {
    **MOVIE_FAVORITE_AUTH_RESPONSES,
    200: {
        "description": (
            "A page of the current user's favorite movies "
            "with matching totals and navigation links."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "favorites": {
                        "summary": "Favorite movies with pagination",
                        "value": movie_favorite_list_response_example,
                    },
                    "filtered_favorites": {
                        "summary": "Filtered and searched favorite movies",
                        "value": movie_favorite_filtered_list_response_example,
                    },
                },
            },
        },
    },
    404: {
        "description": (
            "The favorites list is empty, no movies match the supplied "
            "filters and search, or the requested page has no results."
        ),
        "content": {
            "application/json": {
                "example": {
                    "detail": (
                        "No favorite movies found on this page "
                        "for the supplied filters and search."
                    ),
                },
            },
        },
    },
    422: {
        "description": (
            "Invalid query parameters. Page must be at least 1 and per_page "
            "must be from 1 to 20. Year must be from 1900 to the current year. "
            "IMDb bounds must be from 0 to 10, and imdb_min must not exceed "
            "imdb_max. Genre ID must be at least 1. Text filters and search "
            "must not be blank. Ordering fields must be supported, "
            "nonempty and not repeated."
        ),
    },
    500: {
        "description": "Favorite movies could not be loaded.",
        "content": {
            "application/json": {
                "example": {
                    "detail": (
                        "Unable to load favorite movies. Please try again later."
                    ),
                },
            },
        },
    },
}


ADD_MOVIE_TO_FAVORITES_RESPONSES = {
    **MOVIE_FAVORITE_AUTH_RESPONSES,
    200: {
        "description": (
            "The movie is in the current user's favorites. "
            "First and repeated requests return the same response "
            "without creating duplicate records."
        ),
        "content": {
            "application/json": {
                "example": movie_favorite_response_example,
            },
        },
    },
    404: MOVIE_FAVORITE_NOT_FOUND_RESPONSE,
    422: {
        "description": "Movie ID must be an integer greater than zero.",
    },
    500: {
        "description": "The movie could not be added to favorites.",
        "content": {
            "application/json": {
                "example": {
                    "detail": (
                        "An error occurred while adding the movie to favorites."
                    ),
                },
            },
        },
    },
}


REMOVE_MOVIE_FROM_FAVORITES_RESPONSES = {
    **MOVIE_FAVORITE_AUTH_RESPONSES,
    204: {
        "description": (
            "The movie is absent from the current user's favorites. "
            "Repeated removal also succeeds. No response body."
        ),
    },
    404: MOVIE_FAVORITE_NOT_FOUND_RESPONSE,
    422: {
        "description": "Movie ID must be an integer greater than zero.",
    },
    500: {
        "description": "The movie could not be removed from favorites.",
        "content": {
            "application/json": {
                "example": {
                    "detail": (
                        "An error occurred while removing " "the movie from favorites."
                    ),
                },
            },
        },
    },
}
