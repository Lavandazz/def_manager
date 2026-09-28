from pydantic_settings import BaseSettings, SettingsConfigDict
from config.settings_folders import ENV_FILE, MAIL_ENV_FILE


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

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str

    # JWT токены
    SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ALGORITHM: str

    DEFAULT_PASSWORD: str

    def get_async_db_url(self):
        return (f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_NAME}")
    
    def get_sync_db_url(self):
        return (f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_NAME}")


class MailSettings(BaseSettings):
    """
    Класс для хранения настроек для почты.
    """
    model_config = SettingsConfigDict(env_file=MAIL_ENV_FILE, env_file_encoding="utf-8")

    MAIL_FROM: str
    EMAIL_PASSWORD: str


settings = Settings() # type: ignore
mail_settings = MailSettings() # type: ignore

print("Settings loaded successfully", settings.POSTGRES_HOST)
