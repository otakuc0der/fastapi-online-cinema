from config.settings import BaseAppSettings, Settings


def get_settings() -> BaseAppSettings:
    return Settings()
