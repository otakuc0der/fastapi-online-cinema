from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import StarModel
from exceptions import StarAlreadyExistsError
from schemas import StarCreateSchema, StarUpdateSchema


async def get_star_list(
    db: AsyncSession,
    page: int,
    per_page: int,
) -> list[StarModel]:
    """Get a star page ordered by name and ID."""
    query = (
        select(StarModel)
        .order_by(
            *StarModel.default_order_by(),
            StarModel.id.asc(),
        )
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    result = await db.scalars(query)

    return list(result.all())


async def count_star_records(db: AsyncSession) -> int:
    """Count all star records."""
    total_items = await db.scalar(select(func.count()).select_from(StarModel))

    return total_items or 0


async def get_star_record(
    db: AsyncSession,
    star_id: int,
) -> StarModel | None:
    """Get a star by ID, or None when it does not exist."""
    return await db.scalar(select(StarModel).where(StarModel.id == star_id))


async def star_exists(
    db: AsyncSession,
    name: str,
    exclude_star_id: int | None = None,
) -> bool:
    """Check a case-insensitive name match optionally excluding one star."""
    query = select(StarModel).where(func.lower(StarModel.name) == name.lower())

    if exclude_star_id is not None:
        query = query.where(StarModel.id != exclude_star_id)

    return bool(await db.scalar(select(query.exists())))


async def create_star_record(
    db: AsyncSession,
    star_data: StarCreateSchema,
) -> StarModel:
    """Create a star after a case-insensitive duplicate name check."""
    try:
        already_exists = await star_exists(
            db=db,
            name=star_data.name,
        )

        if already_exists:
            raise StarAlreadyExistsError()

        star = StarModel(name=star_data.name)
        db.add(star)

        await db.commit()

        return star

    except IntegrityError as error:
        await db.rollback()

        constraint_name = getattr(
            error.orig.__cause__,
            "constraint_name",
            None,
        )

        if constraint_name == "stars_name_key":
            raise StarAlreadyExistsError()

        raise

    except SQLAlchemyError:
        await db.rollback()
        raise


async def update_star_record(
    db: AsyncSession,
    star: StarModel,
    star_data: StarUpdateSchema,
) -> StarModel:
    """Rename a star after a case-insensitive duplicate check preserving movie links."""
    try:
        already_exists = await star_exists(
            db=db,
            name=star_data.name,
            exclude_star_id=star.id,
        )

        if already_exists:
            raise StarAlreadyExistsError()

        star.name = star_data.name

        await db.commit()

        return star

    except IntegrityError as error:
        await db.rollback()

        constraint_name = getattr(
            error.orig.__cause__,
            "constraint_name",
            None,
        )

        if constraint_name == "stars_name_key":
            raise StarAlreadyExistsError()

        raise

    except SQLAlchemyError:
        await db.rollback()
        raise


async def delete_star_record(db: AsyncSession, star: StarModel) -> None:
    """Delete a star and association rows while preserving movies."""
    try:
        await db.delete(star)
        await db.commit()

    except SQLAlchemyError:
        await db.rollback()
        raise
