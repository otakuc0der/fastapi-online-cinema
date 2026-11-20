from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import MovieReactionEnum, MovieReactionModel
from exceptions import MovieNotFoundError, UserNotActiveError, UserNotFoundError
from services.account_crud import get_user_by_id_for_update
from services.movie_crud import get_movie_record


async def get_movie_reaction(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
) -> MovieReactionModel | None:
    return await db.scalar(
        select(MovieReactionModel).where(
            MovieReactionModel.movie_id == movie_id,
            MovieReactionModel.user_id == user_id,
        )
    )


async def set_movie_reaction(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
    reaction: MovieReactionEnum,
) -> MovieReactionModel:
    try:
        user = await get_user_by_id_for_update(db=db, user_id=user_id)

        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise UserNotActiveError()

        movie = await get_movie_record(db=db, movie_id=movie_id)

        if movie is None:
            raise MovieNotFoundError()

        reaction_record = await get_movie_reaction(
            db=db,
            user_id=user_id,
            movie_id=movie_id,
        )

        if reaction_record is None:
            reaction_record = MovieReactionModel(
                user_id=user.id,
                movie_id=movie.id,
                reaction=reaction,
            )

            db.add(reaction_record)
        else:
            reaction_record.reaction = reaction

        await db.commit()

        return reaction_record

    except Exception:
        await db.rollback()
        raise


async def delete_movie_reaction(
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

        reaction_record = await get_movie_reaction(
            db=db,
            user_id=user_id,
            movie_id=movie_id,
        )

        if reaction_record is not None:
            await db.delete(reaction_record)

        await db.commit()
    except Exception:
        await db.rollback()
        raise


async def count_movie_reactions(
    db: AsyncSession,
    movie_id: int,
) -> tuple[int, int]:
    likes_count = func.count().filter(
        MovieReactionModel.reaction == MovieReactionEnum.LIKE
    )

    dislikes_count = func.count().filter(
        MovieReactionModel.reaction == MovieReactionEnum.DISLIKE
    )

    query = (
        select(likes_count, dislikes_count)
        .select_from(MovieReactionModel)
        .where(MovieReactionModel.movie_id == movie_id)
    )

    result = await db.execute(query)
    likes, dislikes = result.one()

    return likes, dislikes
