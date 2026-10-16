from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql.elements import UnaryExpression

from database import (
    CertificationModel,
    DirectorModel,
    GenreModel,
    MovieModel,
    StarModel,
)
from exceptions import MovieAlreadyExistsError
from schemas import MovieCreateSchema, MovieUpdateSchema

type ReferenceModel = GenreModel | CertificationModel | StarModel | DirectorModel


def build_movie_ordering(ordering: str | None = None) -> list[UnaryExpression]:
    """Validate ordering fields and build expressions with an ID tie-breaker."""
    sortable_fields = {
        "id": MovieModel.id,
        "price": MovieModel.price,
        "year": MovieModel.year,
        "imdb": MovieModel.imdb,
        "votes": MovieModel.votes,
    }

    if ordering is None:
        return MovieModel.default_order_by()

    ordering_expressions = []
    seen_fields: set[str] = set()

    for item in ordering.split(","):
        item = item.strip()

        if not item:
            raise ValueError("Each ordering item must contain a field name.")

        descending = item.startswith("-")
        field_name = item[1:] if descending else item

        if field_name in seen_fields:
            raise ValueError(f"Ordering field '{field_name}' must not be repeated.")

        if field_name not in sortable_fields:
            raise ValueError(
                f"Unsupported ordering field '{field_name}'. "
                "Allowed fields: id, price, year, imdb, votes."
            )

        seen_fields.add(field_name)
        column = sortable_fields[field_name]
        expression = column.desc() if descending else column.asc()
        ordering_expressions.append(expression)

    if "id" not in seen_fields:
        ordering_expressions.extend(MovieModel.default_order_by())

    return ordering_expressions


def build_movie_query(
    year: int | None = None,
    imdb_min: float | None = None,
    imdb_max: float | None = None,
    genre: str | None = None,
    star: str | None = None,
    director: str | None = None,
    certification: str | None = None,
    search: str | None = None,
) -> Select[tuple[MovieModel]]:
    """Combine movie filters with partial search across titles, descriptions and names."""
    query = select(MovieModel)

    if year is not None:
        query = query.where(MovieModel.year == year)

    if imdb_min is not None:
        query = query.where(MovieModel.imdb >= imdb_min)

    if imdb_max is not None:
        query = query.where(MovieModel.imdb <= imdb_max)

    if genre is not None:
        query = query.where(
            MovieModel.genres.any(func.lower(GenreModel.name) == genre.strip().lower())
        )

    if star is not None:
        query = query.where(
            MovieModel.stars.any(func.lower(StarModel.name) == star.strip().lower())
        )

    if director is not None:
        query = query.where(
            MovieModel.directors.any(
                func.lower(DirectorModel.name) == director.strip().lower()
            )
        )

    if certification is not None:
        query = query.where(
            MovieModel.certification.has(
                func.lower(CertificationModel.name) == certification.strip().lower()
            )
        )

    if search is not None:
        query = query.where(
            or_(
                MovieModel.name.icontains(search, autoescape=True),
                MovieModel.description.icontains(search, autoescape=True),
                MovieModel.stars.any(StarModel.name.icontains(search, autoescape=True)),
                MovieModel.directors.any(
                    DirectorModel.name.icontains(search, autoescape=True)
                ),
            )
        )

    return query


async def get_movie_page(
    db: AsyncSession,
    page: int,
    per_page: int,
    ordering_expressions: list[UnaryExpression],
    year: int | None = None,
    imdb_min: float | None = None,
    imdb_max: float | None = None,
    genre: str | None = None,
    star: str | None = None,
    director: str | None = None,
    certification: str | None = None,
    search: str | None = None,
) -> list[MovieModel]:
    """Fetch a movie page matching filters and search with the supplied ordering."""
    query = build_movie_query(
        year=year,
        imdb_min=imdb_min,
        imdb_max=imdb_max,
        genre=genre,
        star=star,
        director=director,
        certification=certification,
        search=search,
    )

    query = (
        query.order_by(*ordering_expressions)
        .limit(per_page)
        .offset((page - 1) * per_page)
    )

    result = await db.scalars(query)

    return list(result.all())


async def count_movies(
    db: AsyncSession,
    year: int | None = None,
    imdb_min: float | None = None,
    imdb_max: float | None = None,
    genre: str | None = None,
    star: str | None = None,
    director: str | None = None,
    certification: str | None = None,
    search: str | None = None,
) -> int:
    """Count movies matching filters and search before pagination."""
    query = build_movie_query(
        year=year,
        imdb_min=imdb_min,
        imdb_max=imdb_max,
        genre=genre,
        star=star,
        director=director,
        certification=certification,
        search=search,
    )

    total_items = await db.scalar(select(func.count()).select_from(query.subquery()))

    return total_items or 0


async def get_movie_record(db: AsyncSession, movie_id: int) -> MovieModel | None:
    """Get a movie and its related entities, or None when absent."""
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


async def movie_exists(
    db: AsyncSession,
    movie_name: str,
    movie_year: int,
    movie_time: int,
    exclude_movie_id: int | None = None,
) -> bool:
    """Check the unique movie combination, optionally excluding one movie."""
    query = select(MovieModel).where(
        MovieModel.name == movie_name,
        MovieModel.year == movie_year,
        MovieModel.time == movie_time,
    )
    if exclude_movie_id is not None:
        query = query.where(MovieModel.id != exclude_movie_id)
    return bool(await db.scalar(select(query.exists())))


async def get_or_create_named_entity(
    db: AsyncSession, model: type[ReferenceModel], name: str
) -> Any:
    """Get an exact name match or flush a new entity without committing."""
    entity = await db.scalar(select(model).where(model.name == name))
    if entity is not None:
        return entity
    new_entity = model(name=name)
    db.add(new_entity)
    await db.flush()
    return new_entity


async def get_or_create_named_entities(
    db: AsyncSession,
    model: type[ReferenceModel],
    names: list[str],
) -> list[Any]:
    """Resolve related names sequentially within the caller's transaction."""
    return [
        await get_or_create_named_entity(db=db, model=model, name=name)
        for name in names
    ]


async def create_movie_record(
    db: AsyncSession,
    movie_data: MovieCreateSchema,
) -> MovieModel:
    """Create a movie and named relations, commit, then load its details."""
    already_exists = await movie_exists(
        db=db,
        movie_name=movie_data.name,
        movie_year=movie_data.year,
        movie_time=movie_data.time,
    )
    if already_exists:
        raise MovieAlreadyExistsError(
            "A movie with the same name, release year and duration already exists."
        )

    try:
        certification = await get_or_create_named_entity(
            db=db, model=CertificationModel, name=movie_data.certification
        )
        genres = await get_or_create_named_entities(
            db=db, model=GenreModel, names=movie_data.genres
        )
        stars = await get_or_create_named_entities(
            db=db, model=StarModel, names=movie_data.stars
        )
        directors = await get_or_create_named_entities(
            db=db, model=DirectorModel, names=movie_data.directors
        )
        movie_data_dict = movie_data.model_dump(
            exclude={"certification", "genres", "stars", "directors"}
        )
        movie = MovieModel(
            **movie_data_dict,
            certification=certification,
            genres=genres,
            stars=stars,
            directors=directors,
        )
        db.add(movie)
        await db.flush()
        movie_id = movie.id
        await db.commit()

    except IntegrityError as error:
        await db.rollback()
        constraint_name = getattr(error.orig.__cause__, "constraint_name", None)
        if constraint_name == "unique_movie_constraint":
            raise MovieAlreadyExistsError(
                "A movie with the same name, release year and duration already exists."
            )
        raise

    except SQLAlchemyError:
        await db.rollback()
        raise

    loaded_movie = await get_movie_record(db=db, movie_id=movie_id)
    if loaded_movie is None:
        raise RuntimeError("Failed to load the created movie.")
    return loaded_movie


async def update_movie_record(
    db: AsyncSession,
    movie: MovieModel,
    movie_data: MovieUpdateSchema,
) -> MovieModel:
    """Commit supplied scalar changes, preserving omitted fields and relations."""
    changes = movie_data.model_dump(exclude_unset=True)
    if not changes:
        return movie

    try:
        if {"name", "year", "time"} & changes.keys():
            already_exists = await movie_exists(
                db=db,
                movie_name=changes.get("name", movie.name),
                movie_year=changes.get("year", movie.year),
                movie_time=changes.get("time", movie.time),
                exclude_movie_id=movie.id,
            )
            if already_exists:
                raise MovieAlreadyExistsError(
                    "A movie with the same name, release year and duration already exists."
                )
        for field_name, value in changes.items():
            setattr(movie, field_name, value)
        await db.commit()
        return movie

    except IntegrityError as error:
        await db.rollback()
        constraint_name = getattr(error.orig.__cause__, "constraint_name", None)
        if constraint_name == "unique_movie_constraint":
            raise MovieAlreadyExistsError(
                "A movie with the same name, release year and duration already exists."
            )
        raise

    except MovieAlreadyExistsError, SQLAlchemyError:
        await db.rollback()
        raise


async def delete_movie_record(db: AsyncSession, movie: MovieModel) -> None:
    """Delete a movie and association rows while preserving related entities."""
    try:
        await db.delete(movie)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise
