from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    DECIMAL,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base

movie_stars = Table(
    "movie_stars",
    Base.metadata,
    Column(
        "movie_id",
        Integer,
        ForeignKey("movies.id"),
        primary_key=True,
    ),
    Column(
        "star_id",
        Integer,
        ForeignKey("stars.id"),
        primary_key=True,
    ),
)

movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column(
        "movie_id",
        Integer,
        ForeignKey("movies.id"),
        primary_key=True,
    ),
    Column(
        "genre_id",
        Integer,
        ForeignKey("genres.id"),
        primary_key=True,
    ),
)

movie_directors = Table(
    "movie_directors",
    Base.metadata,
    Column(
        "movie_id",
        Integer,
        ForeignKey("movies.id"),
        primary_key=True,
    ),
    Column(
        "director_id",
        Integer,
        ForeignKey("directors.id"),
        primary_key=True,
    ),
)


class StarModel(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list[MovieModel]] = relationship(
        secondary=movie_stars,
        back_populates="stars",
    )

    def __repr__(self) -> str:
        return f"<Star('{self.name}')>"


class GenreModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list[MovieModel]] = relationship(
        secondary=movie_genres,
        back_populates="genres",
    )

    def __repr__(self) -> str:
        return f"<Genre(name='{self.name}')>"


class DirectorModel(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list[MovieModel]] = relationship(
        secondary=movie_directors,
        back_populates="directors",
    )

    def __repr__(self) -> str:
        return f"<Director('{self.name}')>"


class CertificationModel(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list[MovieModel]] = relationship(back_populates="certification")

    def __repr__(self) -> str:
        return f"<Certification('{self.name}')>"


class MovieModel(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), default=uuid4, unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time: Mapped[int] = mapped_column(Integer, nullable=False)
    imdb: Mapped[float] = mapped_column(Float, nullable=False)
    votes: Mapped[int] = mapped_column(Integer, nullable=False)
    meta_score: Mapped[Optional[float]] = mapped_column(Float)
    gross: Mapped[Optional[float]] = mapped_column(Float)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)

    certification_id: Mapped[int] = mapped_column(
        ForeignKey("certifications.id"),
        nullable=False,
    )
    certification: Mapped[CertificationModel] = relationship(
        back_populates="movies",
    )

    stars: Mapped[list[StarModel]] = relationship(
        secondary=movie_stars,
        back_populates="movies",
    )

    genres: Mapped[list[GenreModel]] = relationship(
        secondary=movie_genres,
        back_populates="movies",
    )

    directors: Mapped[list[DirectorModel]] = relationship(
        secondary=movie_directors,
        back_populates="movies",
    )

    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="unique_movie_constraint"),
    )

    @classmethod
    def default_order_by(cls):
        return [cls.id.asc()]

    def __repr__(self) -> str:
        return f"<Movie(id={self.id}, " f"name='{self.name}', year={self.year})>"
