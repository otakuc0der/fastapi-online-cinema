from sqlalchemy import select, exists, insert
from sqlalchemy.ext.asyncio import AsyncSession

from database import user_favorite_movies
from exceptions import UserNotFoundError, UserNotActiveError, MovieNotFoundError
from services.account_crud import get_user_by_id_for_update
from services.movie_crud import get_movie_record


async def is_movie_favorite(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
) -> bool:
    return await db.scalar(
        select(
            exists().where(
                user_favorite_movies.c.user_id == user_id,
                user_favorite_movies.c.movie_id == movie_id,
            )
        )
    )


async def add_movie_to_favorites(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
) -> None:
    try:
        user = await get_user_by_id_for_update(db=db, user_id=user_id)

        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise UserNotActiveError()

        movie = await get_movie_record(db=db, movie_id=movie_id)

        if movie is None:
            raise MovieNotFoundError()

        already_favorite = await is_movie_favorite(
            db=db,
            user_id=user_id,
            movie_id=movie_id,
        )

        if not already_favorite:
            await db.execute(
                user_favorite_movies.insert().values(
                    user_id=user_id,
                    movie_id=movie_id,
                )
            )

        await db.commit()

    except Exception:
        await db.rollback()
        raise


async def remove_movie_from_favorites(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
) -> None:
    try:
        user = await get_user_by_id_for_update(db=db, user_id=user_id)

        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise UserNotActiveError()

        movie = await get_movie_record(db=db, movie_id=movie_id)

        if movie is None:
            raise MovieNotFoundError()

        await db.execute(
            user_favorite_movies.delete().where(
                user_favorite_movies.c.user_id == user_id,
                user_favorite_movies.c.movie_id == movie_id,
            )
        )

        await db.commit()

    except Exception:
        await db.rollback()
        raise
