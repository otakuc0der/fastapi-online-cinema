from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import MovieRatingModel
from exceptions import MovieNotFoundError, UserNotActiveError, UserNotFoundError
from services.account_crud import get_user_by_id_for_update
from services.movie_crud import get_movie_record


async def get_movie_rating(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
) -> MovieRatingModel | None:
    return await db.scalar(
        select(MovieRatingModel).where(
            MovieRatingModel.user_id == user_id,
            MovieRatingModel.movie_id == movie_id,
        )
    )


async def set_movie_rating(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
    rating: int,
) -> MovieRatingModel:
    try:
        user = await get_user_by_id_for_update(db=db, user_id=user_id)

        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise UserNotActiveError()

        movie = await get_movie_record(db=db, movie_id=movie_id)

        if movie is None:
            raise MovieNotFoundError()

        rating_record = await get_movie_rating(
            db=db,
            user_id=user_id,
            movie_id=movie_id,
        )

        if rating_record is None:
            rating_record = MovieRatingModel(
                user_id=user.id,
                movie_id=movie.id,
                rating=rating,
            )

            db.add(rating_record)
        else:
            rating_record.rating = rating

        await db.commit()

        return rating_record

    except Exception:
        await db.rollback()
        raise


async def delete_movie_rating(
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

        rating_record = await get_movie_rating(
            db=db,
            user_id=user_id,
            movie_id=movie_id,
        )

        if rating_record is not None:
            await db.delete(rating_record)

        await db.commit()

    except Exception:
        await db.rollback()
        raise


async def get_movie_rating_summary(
    db: AsyncSession,
    movie_id: int,
) -> tuple[float | None, int]:
    movie = await get_movie_record(db=db, movie_id=movie_id)

    if movie is None:
        raise MovieNotFoundError()

    result = await db.execute(
        select(
            func.avg(MovieRatingModel.rating),
            func.count(MovieRatingModel.id),
        ).where(
            MovieRatingModel.movie_id == movie_id,
        )
    )

    average_rating, ratings_count = result.one()

    return (
        float(average_rating) if average_rating is not None else None,
        ratings_count,
    )


async def get_current_movie_rating(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
) -> MovieRatingModel | None:
    movie = await get_movie_record(db=db, movie_id=movie_id)

    if movie is None:
        raise MovieNotFoundError()

    return await get_movie_rating(
        db=db,
        user_id=user_id,
        movie_id=movie_id,
    )
