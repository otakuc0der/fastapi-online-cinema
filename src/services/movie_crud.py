from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import MovieModel


async def fetch_movies_page(
    db: AsyncSession,
    page: int,
    per_page: int,
) -> list[MovieModel]:
    """Fetch a movie page using the model's default ordering."""
    query = (
        select(MovieModel)
        .limit(per_page)
        .offset((page - 1) * per_page)
        .order_by(*MovieModel.default_order_by())
    )

    result = await db.scalars(query)

    return list(result.all())


async def count_movies(db: AsyncSession) -> int:
    """Count all movies in the catalog."""
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))

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
