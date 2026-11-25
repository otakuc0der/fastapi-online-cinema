from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import MovieCommentModel, UserGroupEnum
from exceptions import (
    MovieCommentNotFoundError,
    MovieCommentPermissionError,
    MovieNotFoundError,
    UserNotActiveError,
    UserNotFoundError,
)
from schemas import MovieCommentCreateSchema, MovieCommentUpdateSchema
from services.account_crud import get_user_by_id_for_update
from services.movie_crud import get_movie_record


async def get_movie_comment(
    db: AsyncSession,
    movie_id: int,
    comment_id: int,
) -> MovieCommentModel | None:
    return await db.scalar(
        select(MovieCommentModel).where(
            MovieCommentModel.movie_id == movie_id,
            MovieCommentModel.id == comment_id,
        )
    )


async def get_movie_comment_page(
    db: AsyncSession,
    movie_id: int,
    page: int,
    per_page: int,
) -> list[MovieCommentModel]:
    return list(
        await db.scalars(
            select(MovieCommentModel)
            .where(
                MovieCommentModel.movie_id == movie_id,
            )
            .limit(per_page)
            .offset((page - 1) * per_page)
            .order_by(
                MovieCommentModel.created_at.desc(),
                MovieCommentModel.id.desc(),
            )
        )
    )


async def count_movie_comments(
    db: AsyncSession,
    movie_id: int,
) -> int:
    return await db.scalar(
        select(func.count())
        .select_from(MovieCommentModel)
        .where(MovieCommentModel.movie_id == movie_id)
    )


async def create_movie_comment(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
    comment_data: MovieCommentCreateSchema,
) -> MovieCommentModel:
    try:
        user = await get_user_by_id_for_update(db=db, user_id=user_id)

        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise UserNotActiveError()

        movie = await get_movie_record(db=db, movie_id=movie_id)

        if movie is None:
            raise MovieNotFoundError()

        comment_record = MovieCommentModel(
            user_id=user.id,
            movie_id=movie.id,
            text=comment_data.text,
        )

        db.add(comment_record)

        await db.flush()
        await db.refresh(comment_record)
        await db.commit()

        return comment_record

    except Exception:
        await db.rollback()
        raise


async def update_movie_comment(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
    comment_id: int,
    comment_data: MovieCommentUpdateSchema,
) -> MovieCommentModel:
    try:
        user = await get_user_by_id_for_update(db=db, user_id=user_id)

        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise UserNotActiveError()

        movie = await get_movie_record(db=db, movie_id=movie_id)

        if movie is None:
            raise MovieNotFoundError()

        comment_record = await get_movie_comment(
            db=db,
            movie_id=movie_id,
            comment_id=comment_id,
        )

        if comment_record is None:
            raise MovieCommentNotFoundError()

        if comment_record.user_id != user_id:
            raise MovieCommentPermissionError()

        comment_record.text = comment_data.text

        await db.flush()
        await db.refresh(comment_record)
        await db.commit()

        return comment_record

    except Exception:
        await db.rollback()
        raise


async def delete_movie_comment(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
    comment_id: int,
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

        comment_record = await get_movie_comment(
            db=db,
            movie_id=movie_id,
            comment_id=comment_id,
        )

        if comment_record is None:
            raise MovieCommentNotFoundError()

        if comment_record.user_id != user_id:
            await db.refresh(user, attribute_names=["group"])

            is_admin = user.group is not None and user.group.name == UserGroupEnum.ADMIN

            if not is_admin:
                raise MovieCommentPermissionError()

        await db.delete(comment_record)
        await db.commit()

    except Exception:
        await db.rollback()
        raise
