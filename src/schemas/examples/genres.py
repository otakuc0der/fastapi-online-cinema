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
