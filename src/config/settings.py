from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseAppSettings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent
    PATH_TO_DB: str = str(BASE_DIR / "database" / "source" / "online_cinema.db")
    PATH_TO_MOVIES_CSV: str = str(
        BASE_DIR / "database" / "seed_data" / "imdb_top_1000.csv"
    )

    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parent / ".env",
        env_file_encoding="utf-8",
    )


class Settings(BaseAppSettings):
    POSTGRES_USER: str = "test_user"
    POSTGRES_PASSWORD: str = "test_password"
    POSTGRES_HOST: str = "test_host"
    POSTGRES_DB_PORT: int = 5432
    POSTGRES_DB: str = "test_db"
