import asyncio
import logging
from decimal import Decimal

import pandas as pd
from sqlalchemy import Table, insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm

from config import get_settings
from database import (
    CertificationModel,
    DirectorModel,
    GenreModel,
    MovieModel,
    StarModel,
    get_db_contextmanager,
    movie_directors,
    movie_genres,
    movie_stars,
)

logger = logging.getLogger(__name__)

type ReferenceModel = GenreModel | CertificationModel | StarModel | DirectorModel
type ReferenceMap = dict[str, ReferenceModel]
type ReferenceMaps = tuple[ReferenceMap, ReferenceMap, ReferenceMap, ReferenceMap]
type MovieRecord = dict[str, object]
type MovieKey = tuple[str, int, int]
type MovieMap = dict[MovieKey, MovieModel]
type AssociationRecord = dict[str, int]


class CSVDatabaseSeeder:
    def __init__(
        self,
        csv_file_path: str,
        db_session: AsyncSession,
        movie_price: Decimal,
    ) -> None:
        self._csv_file_path = csv_file_path
        self._db_session = db_session
        self._movie_price = movie_price

    async def is_db_populated(self) -> bool:
        result = await self._db_session.execute(select(MovieModel).limit(1))
        return result.scalar_one_or_none() is not None

    def _remove_duplicates(self, movies: pd.DataFrame) -> pd.DataFrame:
        unique_columns = ["Series_Title", "Released_Year", "Runtime"]

        unique_movies = movies.drop_duplicates(
            subset=unique_columns,
            keep="last",
        ).reset_index(drop=True)

        logger.info(
            "Removed %d duplicate movie records",
            len(movies) - len(unique_movies),
        )

        return unique_movies

    def _load_and_clean_movies(self) -> pd.DataFrame:
        movies = pd.read_csv(self._csv_file_path)

        logger.info("Loaded %d rows from CSV", len(movies))

        string_columns = movies.select_dtypes(include=["string"]).columns

        for column in tqdm(
            string_columns,
            desc="Trimming whitespace in text columns",
            unit="column",
            colour="green",
        ):
            movies[column] = movies[column].str.strip()

        movies["Released_Year"] = movies["Released_Year"].astype(int)

        movies["Runtime"] = (
            movies["Runtime"].str.replace(" min", "", regex=False).astype(int)
        )

        movies["Certificate"] = (
            movies["Certificate"].fillna("Unknown").replace("", "Unknown")
        )

        movies["Gross"] = pd.to_numeric(
            movies["Gross"].str.replace(",", "", regex=False),
            errors="raise",
        )

        for column in tqdm(
            ["Gross", "Meta_score"],
            desc="Preparing nullable numeric columns",
            unit="column",
            colour="green",
        ):
            movies[column] = movies[column].astype(object)
            movies[column] = movies[column].fillna(None)

        return self._remove_duplicates(movies)

    def _get_all_genres(self, movies: pd.DataFrame) -> set[str]:
        genre_names = set(movies["Genre"].dropna().str.split(",").explode().str.strip())
        genre_names.discard("")
        return genre_names

    def _get_all_stars(self, movies: pd.DataFrame) -> set[str]:
        star_columns = ["Star1", "Star2", "Star3", "Star4"]

        star_names = set(
            pd.concat(
                [
                    movies[column]
                    for column in tqdm(
                        star_columns,
                        desc="Collecting star columns",
                        unit="column",
                        colour="green",
                    )
                ]
            )
            .dropna()
            .str.strip()
        )
        star_names.discard("")
        return star_names

    def _get_all_directors(self, movies: pd.DataFrame) -> set[str]:
        director_names = set(movies["Director"].dropna().str.strip())
        director_names.discard("")
        return director_names

    def _get_all_certifications(self, movies: pd.DataFrame) -> set[str]:
        certification_names = set(movies["Certificate"].dropna().str.strip())
        certification_names.discard("")
        return certification_names

    async def _get_or_create_by_name(
        self,
        model_class: type[ReferenceModel],
        names: set[str],
    ) -> ReferenceMap:
        stmt = select(model_class).where(model_class.name.in_(names))
        result = await self._db_session.execute(stmt)

        objects_by_name = {
            obj.name: obj
            for obj in tqdm(
                result.scalars().all(),
                desc=f"Indexing existing {model_class.__tablename__}",
                unit="record",
                colour="green",
            )
        }

        missing_names = names - set(objects_by_name)

        logger.debug(
            "Table %s: %d existing records found, %d records to create",
            model_class.__tablename__,
            len(objects_by_name),
            len(missing_names),
        )

        if missing_names:
            new_records = [
                {"name": name}
                for name in tqdm(
                    missing_names,
                    desc=f"Preparing new {model_class.__tablename__}",
                    unit="record",
                    colour="green",
                )
            ]

            stmt = insert(model_class).values(new_records).returning(model_class)
            result = await self._db_session.execute(stmt)

            objects_by_name.update(
                {
                    obj.name: obj
                    for obj in tqdm(
                        result.scalars().all(),
                        desc=f"Indexing inserted {model_class.__tablename__}",
                        unit="record",
                        colour="green",
                    )
                }
            )

        return objects_by_name

    async def _prepare_reference_data(self, movies: pd.DataFrame) -> ReferenceMaps:
        genre_names = self._get_all_genres(movies)
        star_names = self._get_all_stars(movies)
        director_names = self._get_all_directors(movies)
        certification_names = self._get_all_certifications(movies)

        genres_by_name = await self._get_or_create_by_name(GenreModel, genre_names)
        stars_by_name = await self._get_or_create_by_name(StarModel, star_names)
        directors_by_name = await self._get_or_create_by_name(
            DirectorModel,
            director_names,
        )
        certifications_by_name = await self._get_or_create_by_name(
            CertificationModel,
            certification_names,
        )

        return (
            genres_by_name,
            stars_by_name,
            directors_by_name,
            certifications_by_name,
        )

    def _build_movie_records(
        self,
        movies: pd.DataFrame,
        certifications_by_name: ReferenceMap,
    ) -> list[MovieRecord]:
        movie_records: list[MovieRecord] = []

        for _, row in tqdm(
            movies.iterrows(),
            total=len(movies),
            desc="Preparing movie records",
            unit="movie",
            colour="green",
        ):
            certification = certifications_by_name[row["Certificate"]]

            movie_record: MovieRecord = {
                "name": row["Series_Title"],
                "year": int(row["Released_Year"]),
                "time": int(row["Runtime"]),
                "imdb": float(row["IMDB_Rating"]),
                "votes": int(row["No_of_Votes"]),
                "meta_score": row["Meta_score"],
                "gross": row["Gross"],
                "description": row["Overview"],
                "price": self._movie_price,
                "certification_id": certification.id,
            }
            movie_records.append(movie_record)

        return movie_records

    async def _get_existing_movie_keys(self) -> set[MovieKey]:
        result = await self._db_session.execute(
            select(MovieModel.name, MovieModel.year, MovieModel.time)
        )

        return {
            (name, year, time)
            for name, year, time in tqdm(
                result.all(),
                desc="Collecting existing movie keys",
                unit="movie",
                colour="green",
            )
        }

    def _filter_new_movie_records(
        self,
        movie_records: list[MovieRecord],
        existing_keys: set[MovieKey],
    ) -> list[MovieRecord]:
        return [
            record
            for record in tqdm(
                movie_records,
                desc="Filtering out existing movies",
                unit="movie",
                colour="green",
            )
            if (record["name"], record["year"], record["time"]) not in existing_keys
        ]

    async def _insert_movies(self, movie_records: list[MovieRecord]) -> MovieMap:
        if not movie_records:
            return {}

        stmt = insert(MovieModel).values(movie_records).returning(MovieModel)
        result = await self._db_session.execute(stmt)

        return {
            (movie.name, movie.year, movie.time): movie
            for movie in tqdm(
                result.scalars().all(),
                desc="Indexing inserted movies",
                unit="movie",
                colour="green",
            )
        }

    def _build_movie_genre_records(
        self,
        movies: pd.DataFrame,
        movies_by_key: MovieMap,
        genres_by_name: ReferenceMap,
    ) -> list[AssociationRecord]:
        movie_genre_records: list[AssociationRecord] = []

        for _, row in tqdm(
            movies.iterrows(),
            total=len(movies),
            desc="Preparing movie-genre associations",
            unit="movie",
            colour="green",
        ):
            movie_key: MovieKey = (
                row["Series_Title"],
                int(row["Released_Year"]),
                int(row["Runtime"]),
            )

            if movie_key not in movies_by_key or pd.isna(row["Genre"]):
                continue

            movie = movies_by_key[movie_key]
            genre_names: set[str] = set()

            for genre_name in row["Genre"].split(","):
                genre_name = genre_name.strip()
                if genre_name:
                    genre_names.add(genre_name)

            for genre_name in genre_names:
                movie_genre_records.append(
                    {
                        "movie_id": movie.id,
                        "genre_id": genres_by_name[genre_name].id,
                    }
                )

        return movie_genre_records

    def _build_movie_star_records(
        self,
        movies: pd.DataFrame,
        movies_by_key: MovieMap,
        stars_by_name: ReferenceMap,
    ) -> list[AssociationRecord]:
        star_columns = ["Star1", "Star2", "Star3", "Star4"]
        movie_star_records: list[AssociationRecord] = []

        for _, row in tqdm(
            movies.iterrows(),
            total=len(movies),
            desc="Preparing movie-star associations",
            unit="movie",
            colour="green",
        ):
            movie_key: MovieKey = (
                row["Series_Title"],
                int(row["Released_Year"]),
                int(row["Runtime"]),
            )

            if movie_key not in movies_by_key:
                continue

            movie = movies_by_key[movie_key]
            star_names: set[str] = set()

            for column in star_columns:
                star_value = row[column]

                if pd.isna(star_value):
                    continue

                star_name = star_value.strip()
                if star_name:
                    star_names.add(star_name)

            for star_name in star_names:
                movie_star_records.append(
                    {
                        "movie_id": movie.id,
                        "star_id": stars_by_name[star_name].id,
                    }
                )

        return movie_star_records

    def _build_movie_director_records(
        self,
        movies: pd.DataFrame,
        movies_by_key: MovieMap,
        directors_by_name: ReferenceMap,
    ) -> list[AssociationRecord]:
        movie_director_records: list[AssociationRecord] = []

        for _, row in tqdm(
            movies.iterrows(),
            total=len(movies),
            desc="Preparing movie-director associations",
            unit="movie",
            colour="green",
        ):
            movie_key: MovieKey = (
                row["Series_Title"],
                int(row["Released_Year"]),
                int(row["Runtime"]),
            )

            if (
                movie_key not in movies_by_key
                or pd.isna(row["Director"])
                or not row["Director"].strip()
            ):
                continue

            movie = movies_by_key[movie_key]
            director_name = row["Director"].strip()

            movie_director_records.append(
                {
                    "movie_id": movie.id,
                    "director_id": directors_by_name[director_name].id,
                }
            )

        return movie_director_records

    async def _insert_associations(
        self,
        table: Table,
        records: list[AssociationRecord],
    ) -> None:
        if not records:
            return

        logger.debug("Inserting %d associations into %s", len(records), table.name)

        await self._db_session.execute(insert(table).values(records))

    async def seed(self) -> None:
        logger.info("Starting movie import from %s", self._csv_file_path)

        try:
            movies = self._load_and_clean_movies()

            logger.info("Prepared %d movie records from CSV", len(movies))

            (
                genres_by_name,
                stars_by_name,
                directors_by_name,
                certifications_by_name,
            ) = await self._prepare_reference_data(movies)

            movie_records = self._build_movie_records(movies, certifications_by_name)

            existing_movie_keys = await self._get_existing_movie_keys()

            new_movie_records = self._filter_new_movie_records(
                movie_records,
                existing_movie_keys,
            )

            logger.info(
                "Movies to insert: %d; existing movies skipped: %d",
                len(new_movie_records),
                len(movie_records) - len(new_movie_records),
            )

            new_movies_by_key = await self._insert_movies(new_movie_records)

            movie_star_records = self._build_movie_star_records(
                movies,
                new_movies_by_key,
                stars_by_name,
            )
            movie_genre_records = self._build_movie_genre_records(
                movies,
                new_movies_by_key,
                genres_by_name,
            )
            movie_director_records = self._build_movie_director_records(
                movies,
                new_movies_by_key,
                directors_by_name,
            )

            logger.info(
                "Prepared associations: %d stars, %d genres, %d directors",
                len(movie_star_records),
                len(movie_genre_records),
                len(movie_director_records),
            )

            await self._insert_associations(movie_stars, movie_star_records)
            await self._insert_associations(movie_genres, movie_genre_records)
            await self._insert_associations(movie_directors, movie_director_records)

            await self._db_session.commit()

            logger.info(
                "Movie import completed successfully: %d movies inserted",
                len(new_movies_by_key),
            )

        except SQLAlchemyError:
            logger.exception(
                "Database error during movie import; " "rolling back transaction"
            )
            await self._db_session.rollback()
            raise

        except Exception:
            logger.exception(
                "Unexpected error during movie import; " "rolling back transaction"
            )
            await self._db_session.rollback()
            raise


async def main() -> None:
    settings = get_settings()

    async with get_db_contextmanager() as session:
        seeder = CSVDatabaseSeeder(
            csv_file_path=settings.PATH_TO_MOVIES_CSV,
            db_session=session,
            movie_price=Decimal("4.99"),
        )

        is_db_populated = await seeder.is_db_populated()

        if is_db_populated:
            logger.info("Database is already populated. Skipping seeding.")
        else:
            try:
                await seeder.seed()
            except SQLAlchemyError:
                logger.error("Database seeding failed.")
                raise
            except Exception:
                logger.error("Movie seeding failed due to an unexpected error.")
                raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    asyncio.run(main())
