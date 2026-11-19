from schemas.examples.security import moderator_error_responses

star_schema_example = {
    "id": 1,
    "name": "Leonardo DiCaprio",
}

star_list_response_example = {
    "stars": [star_schema_example],
    "prev_page": None,
    "next_page": "/api/v1/stars/?per_page=1&page=2",
    "total_pages": 100,
    "total_items": 100,
}

star_create_example = {
    "name": "Leonardo DiCaprio",
}

star_update_example = {
    "name": "Leonardo Wilhelm DiCaprio",
}

star_updated_response_example = {
    **star_schema_example,
    **star_update_example,
}


LIST_STARS_RESPONSES = {
    404: {
        "description": "No actors exist on the requested page.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "No stars found on the requested page.",
                },
            },
        },
    },
    422: {
        "description": (
            "Page must be an integer greater than zero. "
            "Per_page must be an integer from 1 to 20."
        ),
    },
    500: {
        "description": "The actor list could not be loaded.",
    },
}


GET_STAR_RESPONSES = {
    404: {
        "description": "The actor does not exist.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Star with ID 9999 was not found.",
                },
            },
        },
    },
    422: {
        "description": "Star ID must be an integer greater than zero.",
    },
    500: {
        "description": "Actor details could not be loaded.",
    },
}


CREATE_STAR_RESPONSES = {
    **moderator_error_responses,
    409: {
        "description": "An actor record with the same name already exists.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "A star with the same name already exists.",
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
        "description": "The actor could not be created.",
    },
}


UPDATE_STAR_RESPONSES = {
    **moderator_error_responses,
    200: {
        "content": {
            "application/json": {
                "example": star_updated_response_example,
            },
        },
    },
    404: {
        "description": "The actor does not exist.",
    },
    409: {
        "description": "Another actor record already has the requested name.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "A star with the same name already exists.",
                },
            },
        },
    },
    422: {
        "description": (
            "Invalid star ID or name. Name is required and must contain "
            "1–100 characters after trimming. Unknown fields are rejected."
        ),
    },
    500: {
        "description": "The actor could not be updated.",
    },
}


DELETE_STAR_RESPONSES = {
    **moderator_error_responses,
    204: {
        "description": "Actor deleted. No response body.",
    },
    404: {
        "description": "The actor does not exist.",
    },
    422: {
        "description": "Star ID must be an integer greater than zero.",
    },
    500: {
        "description": "The actor could not be deleted.",
    },
}
