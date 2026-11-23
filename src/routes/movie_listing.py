import math

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from routes.dependencies.movies import MovieListParams
from routes.utils import build_pagination_links
from schemas import MovieBaseSchema, MovieListResponseSchema
from services.movie_crud import count_movies, get_movie_page


async def build_movie_page_response(
    request: Request,
    db: AsyncSession,
    params: MovieListParams,
    not_found_message: str,
    favorite_user_id: int | None = None,
) -> MovieListResponseSchema:
    movies = await get_movie_page(
        db=db,
        page=params.page,
        per_page=params.per_page,
        ordering_expressions=params.ordering_expressions,
        year=params.year,
        imdb_min=params.imdb_min,
        imdb_max=params.imdb_max,
        genre=params.genre,
        star=params.star,
        director=params.director,
        certification=params.certification,
        search=params.search,
        genre_id=params.genre_id,
        favorite_user_id=favorite_user_id,
    )

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found_message,
        )

    total_items = await count_movies(
        db=db,
        year=params.year,
        imdb_min=params.imdb_min,
        imdb_max=params.imdb_max,
        genre=params.genre,
        star=params.star,
        director=params.director,
        certification=params.certification,
        search=params.search,
        genre_id=params.genre_id,
        favorite_user_id=favorite_user_id,
    )
    total_pages = math.ceil(total_items / params.per_page)

    query_params = {
        "per_page": params.per_page,
        "page": params.page,
        "year": params.year,
        "imdb_min": params.imdb_min,
        "imdb_max": params.imdb_max,
        "genre": params.genre,
        "star": params.star,
        "director": params.director,
        "certification": params.certification,
        "ordering": params.ordering,
        "search": params.search,
        "genre_id": params.genre_id,
    }

    prev_page_link, next_page_link = build_pagination_links(
        path=request.url.path,
        page=params.page,
        total_pages=total_pages,
        query_params=query_params,
    )

    return MovieListResponseSchema(
        movies=[MovieBaseSchema.model_validate(movie) for movie in movies],
        prev_page=prev_page_link,
        next_page=next_page_link,
        total_pages=total_pages,
        total_items=total_items,
    )
