from fastapi import FastAPI

from routes import (
    account_router,
    genre_router,
    movie_router,
    profile_router,
    star_router,
)

tags_metadata = [
    {
        "name": "movies",
        "description": (
            "Browse, search, filter and sort movies. "
            "View details and manage catalog records."
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
    {
        "name": "accounts",
        "description": (
            "Register and activate accounts, manage authentication and passwords. "
            "Activate users and change their groups as an administrator."
        ),
    },
    {
        "name": "profiles",
        "description": (
            "Create, view, update and delete profiles. "
            "Upload, replace and remove avatars."
        ),
    },
]

app = FastAPI(
    title="Online Cinema API",
    description=(
        "Movie catalog with search, filtering and sorting, "
        "user authentication, role-based access and profiles with avatars."
    ),
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

app.include_router(
    account_router,
    prefix=f"{api_version_prefix}/accounts",
    tags=["accounts"],
)

app.include_router(
    profile_router,
    prefix=f"{api_version_prefix}/profiles",
    tags=["profiles"],
)
