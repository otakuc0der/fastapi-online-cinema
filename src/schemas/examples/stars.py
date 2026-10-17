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
