certification_schema_example = {
    "id": 1,
    "name": "PG-13",
}

genre_schema_example = {
    "id": 1,
    "name": "Action",
}

star_schema_example = {
    "id": 1,
    "name": "Leonardo DiCaprio",
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
        "/api/v1/movies/?per_page=1&page=2" "&year=2010&imdb_min=8.0&imdb_max=9.0"
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
        "An old-school, rebellious pilot returns to a "
        "top flight school to train a new team of young "
        "aviators for a dangerous, near-impossible mission."
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
