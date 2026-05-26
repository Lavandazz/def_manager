from pydantic_settings import BaseSettings, SettingsConfigDict
from config.settings_folders import ENV_FILE


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


    # JWT токены
    SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ALGORITHM: str

    def get_async_db_url(self):
        return (f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_NAME}")
    
    def get_sync_db_url(self):
        return (f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_NAME}")


settings = Settings() # type: ignore

print("Settings loaded successfully", settings.POSTGRES_HOST)
