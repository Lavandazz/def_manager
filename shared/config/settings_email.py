from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.config.settings_folders import MAIL_ENV_FILE


class MailSettings(BaseSettings):
    """
    Класс для хранения настроек для почты.
    """
    model_config = SettingsConfigDict(env_file=MAIL_ENV_FILE, env_file_encoding="utf-8")

    MAIL_FROM: str
    EMAIL_PASSWORD: str


settings = Settings() # type: ignore
mail_settings = MailSettings() # type: ignore