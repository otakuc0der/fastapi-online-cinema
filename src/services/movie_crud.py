from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import MovieModel


async def fetch_movies_page(
    db: AsyncSession,
    page: int,
    per_page: int,
) -> list[MovieModel]:
    query = (
        select(MovieModel)
        .limit(per_page)
        .offset((page - 1) * per_page)
        .order_by(*MovieModel.default_order_by())
    )
    result = await db.scalars(query)

    return list(result.all())


async def count_movies(db: AsyncSession) -> int:
    return await db.scalar(
        select(func.count())
        .select_from(MovieModel)
    )
