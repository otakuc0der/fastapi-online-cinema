from fastapi import status

from schemas.examples.genres import genre_schema_example
from schemas.examples.security import moderator_error_responses
from schemas.examples.stars import star_schema_example

certification_schema_example = {
    "id": 1,
    "name": "PG-13",
}

director_schema_example = {
    "id": 1,
    "name": "Christopher Nolan",
}

genres_schema_example = [
    genre_schema_example,
    {"id": 2, "name": "Adventure"},
    {"id": 3, "name": "Sci-Fi"},
]

stars_schema_example = [
    star_schema_example,
    {"id": 2, "name": "Joseph Gordon-Levitt"},
    {"id": 3, "name": "Elliot Page"},
    {"id": 4, "name": "Ken Watanabe"},
]

directors_schema_example = [director_schema_example]

movie_list_item_example = {
    "id": 1000,
    "uuid": "f82e9f31-7d9c-4f87-a403-65498d62c8c7",
    "name": "Inception",
    "year": 2010,
    "time": 148,
    "imdb": 8.8,
    "price": "4.99",
}

movie_list_response_example = {
    "movies": [movie_list_item_example],
    "prev_page": None,
    "next_page": "/api/v1/movies/?per_page=1&page=2",
    "total_pages": 1000,
    "total_items": 1000,
}

movie_filtered_list_response_example = {
    "movies": [movie_list_item_example],
    "prev_page": None,
    "next_page": (
        "/api/v1/movies/?per_page=1&page=2&year=2010&imdb_min=8.0&imdb_max=9.0"
    ),
    "total_pages": 5,
    "total_items": 5,
}

movie_create_example = {
    "name": "Inception",
    "year": 2010,
    "time": 148,
    "imdb": 8.8,
    "price": "4.99",
    "votes": 2343110,
    "meta_score": 74.0,
    "gross": 292576195.0,
    "description": (
        "A thief who enters people's dreams "
        "is hired to plant an idea "
        "in the mind of a business heir."
    ),
    "certification": "PG-13",
    "genres": [
        "Action",
        "Adventure",
        "Sci-Fi",
    ],
    "stars": [
        "Leonardo DiCaprio",
        "Joseph Gordon-Levitt",
        "Elliot Page",
        "Ken Watanabe",
    ],
    "directors": [
        "Christopher Nolan",
    ],
}

movie_detail_example = {
    **movie_list_item_example,
    "votes": movie_create_example["votes"],
    "meta_score": movie_create_example["meta_score"],
    "gross": movie_create_example["gross"],
    "description": movie_create_example["description"],
    "certification": certification_schema_example,
    "genres": genres_schema_example,
    "stars": stars_schema_example,
    "directors": directors_schema_example,
}

movie_update_example = {"price": "6.99", "meta_score": None}

movie_updated_detail_example = {**movie_detail_example, **movie_update_example}

movie_related_filters_response_example = {
    "movies": [movie_list_item_example],
    "prev_page": None,
    "next_page": (
        "/api/v1/movies/?per_page=1&page=2"
        "&genre=Action"
        "&star=Leonardo DiCaprio"
        "&director=Christopher Nolan"
        "&certification=PG-13"
    ),
    "total_pages": 2,
    "total_items": 2,
}

movie_ordered_list_response_example = {
    "movies": [movie_list_item_example],
    "prev_page": None,
    "next_page": "/api/v1/movies/?per_page=1&page=2&ordering=price,-year",
    "total_pages": 1000,
    "total_items": 1000,
}

movie_search_response_example = {
    "movies": [movie_list_item_example],
    "prev_page": None,
    "next_page": None,
    "total_pages": 1,
    "total_items": 1,
}


LIST_MOVIES_RESPONSES = {
    status.HTTP_200_OK: {
        "content": {
            "application/json": {
                "examples": {
                    "catalog": {
                        "summary": "Without filters",
                        "description": (
                            "page=1, per_page=1. Default ordering: -id. "
                            "Illustrative data and totals."
                        ),
                        "value": movie_list_response_example,
                    },
                    "related_filters": {
                        "summary": "Genre, actor, director and certification",
                        "description": (
                            "page=1, per_page=1, genre=Action, "
                            "star=Leonardo DiCaprio, director=Christopher Nolan, "
                            "certification=PG-13. All filters apply together. "
                            "Illustrative data and totals."
                        ),
                        "value": movie_related_filters_response_example,
                    },
                    "filtered_catalog": {
                        "summary": "Year and IMDb range",
                        "description": (
                            "page=1, per_page=1, year=2010, "
                            "imdb_min=8, imdb_max=9. "
                            "Illustrative data and totals."
                        ),
                        "value": movie_filtered_list_response_example,
                    },
                    "ordered_catalog": {
                        "summary": "Price ascending, then year descending",
                        "description": (
                            "page=1, per_page=1, ordering=price,-year. "
                            "Descending ID resolves remaining ties. "
                            "Illustrative data and totals."
                        ),
                        "value": movie_ordered_list_response_example,
                    },
                    "search_results": {
                        "summary": "Search by part of a movie title",
                        "description": (
                            "page=1, per_page=1, search=incep. "
                            "Matches Inception by title. "
                            "Illustrative data and totals."
                        ),
                        "value": movie_search_response_example,
                    },
                },
            },
        },
    },
    status.HTTP_404_NOT_FOUND: {
        "description": (
            "No movies on the requested page for the supplied filters and search."
        ),
        "content": {
            "application/json": {
                "example": {
                    "detail": (
                        "No movies found on this page "
                        "for the supplied filters and search."
                    ),
                },
            },
        },
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "description": (
            "Invalid parameters. Page and genre_id must be integers greater than "
            "or equal to 1. Per_page must be an integer from 1 to 20. "
            "Year must be an integer from 1900 to the current year. "
            "IMDb bounds must be numbers from 0 to 10. When both are supplied, "
            "imdb_min must not exceed imdb_max. "
            "Name filters and search must contain non-whitespace text. "
            "Ordering accepts comma-separated fields: id, price, year, imdb and votes, "
            "optionally prefixed with '-' for descending order. "
            "Empty ordering items, unsupported fields and repeated fields are rejected."
        ),
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "description": "The movie catalog could not be loaded.",
        "content": {
            "application/json": {
                "example": {
                    "detail": (
                        "Unable to load the movie catalog. " "Please try again later."
                    ),
                },
            },
        },
    },
}


GET_MOVIE_RESPONSES = {
    200: {
        "content": {
            "application/json": {
                "example": movie_detail_example,
            },
        },
    },
    404: {
        "description": "No movie exists with this ID.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Movie with ID 1001 was not found.",
                },
            },
        },
    },
    422: {
        "description": "Movie ID must be an integer greater than or equal to 1.",
    },
    500: {
        "description": "Movie details could not be loaded.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Unable to load movie details. Please try again later.",
                },
            },
        },
    },
}


CREATE_MOVIE_RESPONSES = {
    **moderator_error_responses,
    201: {
        "content": {
            "application/json": {
                "example": movie_detail_example,
            },
        },
    },
    409: {
        "description": "The name, release year and duration match another movie.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "A movie with the same name, release year and duration already exists.",
                },
            },
        },
    },
    422: {
        "description": (
            "Invalid or missing fields. Year must be from 1900 to the current year. "
            "Duration must be positive. IMDb must be from 0 to 10, and meta_score "
            "from 0 to 100. Votes, gross and price must be non-negative. "
            "Price allows up to eight integer digits and two decimal places. "
            "Movie name must contain 1–250 characters after trimming. "
            "Description must not be blank. Related names must contain "
            "1–100 characters after trimming. Duplicate names within each relation "
            "list are rejected regardless of case. Unknown fields are rejected. "
            "Only meta_score and gross accept null."
        ),
    },
    500: {
        "description": "The movie could not be created or its response could not be loaded.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Unable to create the movie. Please try again later.",
                },
            },
        },
    },
}


UPDATE_MOVIE_RESPONSES = {
    **moderator_error_responses,
    200: {
        "content": {
            "application/json": {
                "example": movie_updated_detail_example,
            },
        },
    },
    404: {
        "description": "No movie exists with this ID.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Movie with ID 1001 was not found.",
                },
            },
        },
    },
    409: {
        "description": "The name, release year and duration match another movie.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "A movie with the same name, release year and duration already exists.",
                },
            },
        },
    },
    422: {
        "description": (
            "Invalid ID or update data: empty body, unknown fields, "
            "invalid values, or null supplied for a field other than "
            "meta_score or gross."
        ),
    },
    500: {
        "description": "The movie could not be updated.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Unable to update the movie. Please try again later.",
                },
            },
        },
    },
}


DELETE_MOVIE_RESPONSES = {
    **moderator_error_responses,
    204: {
        "description": "Movie deleted successfully. The response body is empty.",
    },
    404: {
        "description": "No movie exists with this ID.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Movie with ID 1001 was not found.",
                },
            },
        },
    },
    422: {
        "description": "Movie ID must be an integer greater than or equal to 1.",
    },
    500: {
        "description": "The movie could not be deleted.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Unable to delete the movie. Please try again later.",
                },
            },
        },
    },
}
