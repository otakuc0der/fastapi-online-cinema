from fastapi import FastAPI

from routes import movie_router


tags_metadata = [
    {
        "name": "movies",
        "description": (
            "Browse the movie catalog and view movie information."
        ),
    },
]

app = FastAPI(
    title="Online Cinema API",
    description=(
        "Online cinema API with a movie catalog, user accounts\n\n"
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
