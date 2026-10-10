"""Illustrative movie response examples for OpenAPI documentation."""

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
        "/api/v1/movies/?per_page=1&page=2" "&year=2010&imdb_min=8.0&imdb_max=9.0"
    ),
    "total_pages": 5,
    "total_items": 5,
}

movie_detail_example = {
    **movie_list_item_example,
    "votes": 2343110,
    "meta_score": 74.0,
    "gross": 292576195.0,
    "description": (
        "A thief who steals corporate secrets through dream-sharing technology "
        "is tasked with planting an idea in the mind of a business heir."
    ),
    "certification": {
        "id": 1,
        "name": "PG-13",
    },
    "genres": [
        {"id": 1, "name": "Action"},
        {"id": 2, "name": "Adventure"},
        {"id": 3, "name": "Sci-Fi"},
    ],
    "stars": [
        {"id": 1, "name": "Leonardo DiCaprio"},
        {"id": 2, "name": "Joseph Gordon-Levitt"},
        {"id": 3, "name": "Elliot Page"},
        {"id": 4, "name": "Ken Watanabe"},
    ],
    "directors": [
        {"id": 1, "name": "Christopher Nolan"},
    ],
}
