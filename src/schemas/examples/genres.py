from schemas.examples.security import moderator_error_responses

genre_schema_example = {
    "id": 1,
    "name": "Action",
}

genre_list_item_example = {
    **genre_schema_example,
    "movie_count": 120,
}

genre_list_response_example = [
    genre_list_item_example,
    {
        "id": 2,
        "name": "Adventure",
        "movie_count": 85,
    },
    {
        "id": 3,
        "name": "Drama",
        "movie_count": 0,
    },
]

genre_create_example = {
    "name": "Action",
}

genre_update_example = {
    "name": "Adventure",
}

genre_updated_response_example = {
    **genre_schema_example,
    **genre_update_example,
}


LIST_GENRES_RESPONSES = {
    200: {
        "content": {
            "application/json": {
                "example": genre_list_response_example,
            },
        },
    },
    500: {
        "description": "The genre list could not be loaded.",
        "content": {
            "application/json": {
                "example": {
                    "detail": (
                        "Unable to load the genre list. " "Please try again later."
                    ),
                },
            },
        },
    },
}


GET_GENRE_RESPONSES = {
    404: {
        "description": "The genre does not exist.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Genre with ID 9999 was not found.",
                },
            },
        },
    },
    422: {
        "description": "Genre ID must be an integer greater than zero.",
    },
    500: {
        "description": "Genre details could not be loaded.",
    },
}


CREATE_GENRE_RESPONSES = {
    **moderator_error_responses,
    409: {
        "description": "A genre with the same name already exists.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "A genre with the same name already exists.",
                },
            },
        },
    },
    422: {
        "description": (
            "Name is missing, is not a string, is blank after trimming, "
            "or exceeds 100 characters; or unknown fields were supplied."
        ),
    },
    500: {
        "description": "The genre could not be created.",
    },
}


UPDATE_GENRE_RESPONSES = {
    **moderator_error_responses,
    200: {
        "content": {
            "application/json": {
                "example": genre_updated_response_example,
            },
        },
    },
    404: {
        "description": "The genre does not exist.",
    },
    409: {
        "description": "Another genre already has the requested name.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "A genre with the same name already exists.",
                },
            },
        },
    },
    422: {
        "description": (
            "Invalid genre ID or name. Name is required and must contain "
            "1–100 characters after trimming. Unknown fields are rejected."
        ),
    },
    500: {
        "description": "The genre could not be updated.",
    },
}


DELETE_GENRE_RESPONSES = {
    **moderator_error_responses,
    204: {
        "description": "Genre deleted. No response body.",
    },
    404: {
        "description": "The genre does not exist.",
    },
    422: {
        "description": "Genre ID must be an integer greater than zero.",
    },
    500: {
        "description": "The genre could not be deleted.",
    },
}
