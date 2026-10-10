from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import MovieModel


def filter_movie_query(
    year: int | None = None,
    imdb_min: float | None = None,
    imdb_max: float | None = None,
) -> Select[tuple[MovieModel]]:
    """Build a movie query with an optional release year and inclusive IMDb bounds."""
    query = select(MovieModel)

    if year is not None:
        query = query.where(MovieModel.year == year)

    if imdb_min is not None:
        query = query.where(MovieModel.imdb >= imdb_min)

    if imdb_max is not None:
        query = query.where(MovieModel.imdb <= imdb_max)

    return query


async def fetch_movies_page(
    db: AsyncSession,
    page: int,
    per_page: int,
    year: int | None = None,
    imdb_min: float | None = None,
    imdb_max: float | None = None,
) -> list[MovieModel]:
    """Fetch a filtered movie page using the model's default ordering."""
    query = filter_movie_query(year=year, imdb_min=imdb_min, imdb_max=imdb_max)

    query = (
        query.limit(per_page)
        .offset((page - 1) * per_page)
        .order_by(*MovieModel.default_order_by())
    )

    result = await db.scalars(query)

    return list(result.all())


async def count_movies(
    db: AsyncSession,
    year: int | None = None,
    imdb_min: float | None = None,
    imdb_max: float | None = None,
) -> int:
    """Count all movies matching the release year and IMDb filters, without pagination."""
    query = filter_movie_query(year=year, imdb_min=imdb_min, imdb_max=imdb_max)

    total_items = await db.scalar(select(func.count()).select_from(query.subquery()))

    return total_items or 0


async def get_movie_record_by_id(
    db: AsyncSession,
    movie_id: int,
) -> MovieModel | None:
    """Fetch a movie with its related entities, or return None if it does not exist."""
    return await db.scalar(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.certification),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.stars),
            selectinload(MovieModel.directors),
        )
    )
