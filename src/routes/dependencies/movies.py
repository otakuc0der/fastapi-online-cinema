import datetime
from dataclasses import dataclass
from typing import Annotated

from fastapi import HTTPException, Query, status
from sqlalchemy.sql.elements import UnaryExpression

from routes.utils import normalize_optional_text
from services.movie_crud import build_movie_ordering


@dataclass
class MovieListParams:
    year: int | None
    imdb_min: float | None
    imdb_max: float | None
    genre_id: int | None
    genre: str | None
    star: str | None
    director: str | None
    certification: str | None
    ordering: str | None
    search: str | None
    page: int
    per_page: int
    ordering_expressions: list[UnaryExpression]


def get_movie_list_params(
    year: Annotated[
        int | None,
        Query(
            title="Release year",
            description="Exact release year, from 1900 to the current year.",
            ge=1900,
            examples=[2010],
        ),
    ] = None,
    imdb_min: Annotated[
        float | None,
        Query(
            title="Minimum IMDb rating",
            description=(
                "Inclusive minimum, from 0 to 10. "
                "Must not exceed imdb_max when both are provided."
            ),
            ge=0,
            le=10,
            examples=[8.0],
        ),
    ] = None,
    imdb_max: Annotated[
        float | None,
        Query(
            title="Maximum IMDb rating",
            description=(
                "Inclusive maximum, from 0 to 10. "
                "Must not be less than imdb_min when both are provided."
            ),
            ge=0,
            le=10,
            examples=[9.0],
        ),
    ] = None,
    genre_id: Annotated[
        int | None,
        Query(
            title="Genre ID",
            description=(
                "Filter movies by an associated genre ID. Must be at least 1. "
                "Combines with all other filters. If genre is also supplied, "
                "both conditions must match, possibly through different genres. "
                "An unknown ID or no matching movies returns 404."
            ),
            ge=1,
            examples=[1],
        ),
    ] = None,
    genre: Annotated[
        str | None,
        Query(
            title="Genre name",
            description=(
                "Exact genre name, ignoring case and surrounding whitespace. "
                "Optional. Must not be blank."
            ),
            examples=["Action"],
        ),
    ] = None,
    star: Annotated[
        str | None,
        Query(
            title="Actor name",
            description=(
                "Exact actor name, ignoring case and surrounding whitespace. "
                "Optional. Must not be blank."
            ),
            examples=["Leonardo DiCaprio"],
        ),
    ] = None,
    director: Annotated[
        str | None,
        Query(
            title="Director name",
            description=(
                "Exact director name, ignoring case and surrounding whitespace. "
                "Optional. Must not be blank."
            ),
            examples=["Christopher Nolan"],
        ),
    ] = None,
    certification: Annotated[
        str | None,
        Query(
            title="Certification name",
            description=(
                "Exact certification name, ignoring case and surrounding "
                "whitespace. Optional. Must not be blank."
            ),
            examples=["PG-13"],
        ),
    ] = None,
    ordering: Annotated[
        str | None,
        Query(
            title="Movie ordering",
            description=(
                "Comma-separated fields in priority order: id, price, year, "
                "imdb, votes (IMDb vote count). Ascending by default; prefix "
                "with '-' for descending. Surrounding whitespace is ignored. "
                "Empty items, unsupported fields and repeated fields are "
                "rejected. Default: -id. Descending ID is added as a final "
                "tie-breaker unless ID is supplied."
            ),
            examples=["price,-year", "-votes", "-imdb,price"],
        ),
    ] = None,
    search: Annotated[
        str | None,
        Query(
            title="Movie search",
            description=(
                "Case-insensitive partial match in the title, description, "
                "actor or director names. A match in any field is sufficient. "
                "The text is matched as one phrase; surrounding whitespace "
                "is ignored. % and _ are literal characters. Must not be "
                "blank. If omitted, no text search is applied."
            ),
            examples=["incep", "dream", "DiCaprio", "Nolan"],
        ),
    ] = None,
    page: Annotated[
        int,
        Query(
            title="Page number",
            description="Page number, starting from 1. Default: 1.",
            ge=1,
        ),
    ] = 1,
    per_page: Annotated[
        int,
        Query(
            title="Movies per page",
            description="Movies per page, from 1 to 20. Default: 10.",
            ge=1,
            le=20,
        ),
    ] = 10,
) -> MovieListParams:
    current_year = datetime.date.today().year

    if year is not None and year > current_year:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Release year cannot be later than the current year "
                f"({current_year})."
            ),
        )

    if imdb_min is not None and imdb_max is not None and imdb_min > imdb_max:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "Minimum IMDb rating (imdb_min) cannot be greater than "
                "maximum IMDb rating (imdb_max)."
            ),
        )

    name_filters = {
        field_name: normalize_optional_text(
            value,
            error_message=(
                f"Filter '{field_name}' must not be empty "
                "or contain only whitespace."
            ),
        )
        for field_name, value in {
            "genre": genre,
            "star": star,
            "director": director,
            "certification": certification,
        }.items()
    }

    try:
        ordering_expressions = build_movie_ordering(ordering)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    search = normalize_optional_text(
        search,
        error_message="Search query must not be empty or contain only whitespace.",
    )

    return MovieListParams(
        year=year,
        imdb_min=imdb_min,
        imdb_max=imdb_max,
        genre_id=genre_id,
        genre=name_filters["genre"],
        star=name_filters["star"],
        director=name_filters["director"],
        certification=name_filters["certification"],
        ordering=ordering,
        search=search,
        page=page,
        per_page=per_page,
        ordering_expressions=ordering_expressions,
    )
