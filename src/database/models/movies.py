from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    DECIMAL,
    CheckConstraint,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base

if TYPE_CHECKING:
    from database.models.accounts import UserModel


user_favorite_movies = Table(
    "user_favorite_movies",
    Base.metadata,
    Column(
        "movie_id",
        Integer,
        ForeignKey(
            "movies.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Column(
        "user_id",
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)


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

    @classmethod
    def default_order_by(cls):
        return [cls.name.asc()]

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

    @classmethod
    def default_order_by(cls):
        return [cls.name.asc()]

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

    reactions: Mapped[list["MovieReactionModel"]] = relationship(
        "MovieReactionModel",
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    ratings: Mapped[list["MovieRatingModel"]] = relationship(
        "MovieRatingModel",
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    comments: Mapped[list["MovieCommentModel"]] = relationship(
        "MovieCommentModel",
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    favorited_by: Mapped[list["UserModel"]] = relationship(
        secondary=user_favorite_movies,
        back_populates="favorite_movies",
    )

    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="unique_movie_constraint"),
    )

    @classmethod
    def default_order_by(cls):
        return [cls.id.desc()]

    def __repr__(self) -> str:
        return f"<Movie(id={self.id}, " f"name='{self.name}', year={self.year})>"


class MovieReactionEnum(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"


class MovieReactionModel(Base):
    __tablename__ = "movie_reactions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False,
    )
    reaction: Mapped[MovieReactionEnum] = mapped_column(
        SQLEnum(MovieReactionEnum),
        nullable=False,
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="reactions",
    )
    movie: Mapped["MovieModel"] = relationship(
        "MovieModel",
        back_populates="reactions",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "movie_id",
            name="unique_user_movie_reaction",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<MovieReactionModel(id={self.id}, "
            f"user_id={self.user_id}, movie_id={self.movie_id}, "
            f"reaction={self.reaction})>"
        )


class MovieRatingModel(Base):
    __tablename__ = "movie_ratings"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="ratings",
    )
    movie: Mapped["MovieModel"] = relationship(
        "MovieModel",
        back_populates="ratings",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "movie_id",
            name="unique_user_movie_rating",
        ),
        CheckConstraint(
            "rating >= 1 AND rating <= 10",
            name="check_movie_rating",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<MovieRatingModel(id={self.id}, "
            f"user_id={self.user_id}, movie_id={self.movie_id}, "
            f"rating={self.rating})>"
        )


class MovieCommentModel(Base):
    __tablename__ = "movie_comments"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="comments",
    )
    movie: Mapped["MovieModel"] = relationship(
        "MovieModel",
        back_populates="comments",
    )

    def __repr__(self) -> str:
        comment_content = self.text

        if len(comment_content) > 30:
            comment_content = comment_content[:30] + "..."

        return (
            f"<MovieCommentModel(id={self.id}, "
            f"user_id={self.user_id}, movie_id={self.movie_id}, "
            f"comment={comment_content!r})>"
        )
