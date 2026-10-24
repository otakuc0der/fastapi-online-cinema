from fastapi import FastAPI

from routes import genre_router, movie_router, star_router

tags_metadata = [
    {
        "name": "movies",
        "description": (
            "Browse, search, filter and sort the movie catalog. "
            "View movie details and manage movie records."
        ),
    },
    {
        "name": "genres",
        "description": (
            "Browse genres with movie counts. "
            "View, create, rename and delete genres."
        ),
    },
    {
        "name": "stars",
        "description": (
            "Browse actors with pagination. "
            "View, create, rename and delete actor records."
        ),
    },
]

app = FastAPI(
    title="Online Cinema API",
    description="Online cinema API with a movie catalog, user accounts\n\n",
    version="0.1.0",
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        "displayRequestDuration": True,
        "defaultModelsExpandDepth": 0,
        "filter": True,
        "docExpansion": "list",
        "deepLinking": True,
    },
)

api_version_prefix = "/api/v1"

app.include_router(
    movie_router,
    prefix=api_version_prefix,
    tags=["movies"],
)

app.include_router(
    genre_router,
    prefix=api_version_prefix,
    tags=["genres"],
)

app.include_router(
    star_router,
    prefix=api_version_prefix,
    tags=["stars"],
)
