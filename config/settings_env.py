
from pydantic_settings import BaseSettings, SettingsConfigDict

from settings_folders import ENV_FILE

class Settings(BaseSettings):
    """
    Класс для хранения настроек приложения.
    Содержит настройки для подключения к базе данных, настройки для парсера и другие общие настройки.
    """
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8")

    POSTGRES_NAME: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int


settings = Settings()
