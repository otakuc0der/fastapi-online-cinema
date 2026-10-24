from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import GenreModel, MovieModel
from exceptions import GenreAlreadyExistsError
from schemas import GenreCreateSchema, GenreUpdateSchema


async def get_genre_list(
    db: AsyncSession,
) -> list[tuple[GenreModel, int]]:
    """Get all genres with movie counts, including genres without movies."""
    query = (
        select(
            GenreModel,
            func.count(MovieModel.id).label("movie_count"),
        )
        .outerjoin(GenreModel.movies)
        .group_by(GenreModel.id, GenreModel.name)
        .order_by(
            *GenreModel.default_order_by(),
            GenreModel.id.asc(),
        )
    )

    result = await db.execute(query)

    return [(genre, movie_count) for genre, movie_count in result.all()]


async def get_genre_record(
    db: AsyncSession,
    genre_id: int,
) -> GenreModel | None:
    """Get a genre by ID, or None when it does not exist."""
    return await db.scalar(select(GenreModel).where(GenreModel.id == genre_id))


async def genre_exists(
    db: AsyncSession,
    name: str,
    exclude_genre_id: int | None = None,
) -> bool:
    """Check a case-insensitive name match, optionally excluding one genre."""
    query = select(GenreModel).where(func.lower(GenreModel.name) == name.lower())

    if exclude_genre_id is not None:
        query = query.where(GenreModel.id != exclude_genre_id)

    return bool(await db.scalar(select(query.exists())))


async def create_genre_record(
    db: AsyncSession,
    genre_data: GenreCreateSchema,
) -> GenreModel:
    """Create a genre after checking for an existing name without regard to case."""
    try:
        already_exists = await genre_exists(
            db=db,
            name=genre_data.name,
        )

        if already_exists:
            raise GenreAlreadyExistsError()

        genre = GenreModel(name=genre_data.name)
        db.add(genre)

        await db.commit()

        return genre

    except IntegrityError as error:
        await db.rollback()

        constraint_name = getattr(
            error.orig.__cause__,
            "constraint_name",
            None,
        )

        if constraint_name == "genres_name_key":
            raise GenreAlreadyExistsError()

        raise

    except SQLAlchemyError:
        await db.rollback()
        raise


async def update_genre_record(
    db: AsyncSession,
    genre: GenreModel,
    genre_data: GenreUpdateSchema,
) -> GenreModel:
    """Rename a genre after a case-insensitive duplicate check preserving movie links."""
    try:
        already_exists = await genre_exists(
            db=db,
            name=genre_data.name,
            exclude_genre_id=genre.id,
        )

        if already_exists:
            raise GenreAlreadyExistsError()

        genre.name = genre_data.name

        await db.commit()

        return genre

    except IntegrityError as error:
        await db.rollback()

        constraint_name = getattr(
            error.orig.__cause__,
            "constraint_name",
            None,
        )

        if constraint_name == "genres_name_key":
            raise GenreAlreadyExistsError()

        raise

    except SQLAlchemyError:
        await db.rollback()
        raise


async def delete_genre_record(
    db: AsyncSession,
    genre: GenreModel,
) -> None:
    """Delete a genre and its association rows while preserving movies."""
    try:
        await db.delete(genre)
        await db.commit()

    except SQLAlchemyError:
        await db.rollback()
        raise
