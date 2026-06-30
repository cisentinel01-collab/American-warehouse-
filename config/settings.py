import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Enterprise WMS ERP"
    DEBUG: bool = False
    VERSION: str = "2.0.0"

    # Database Settings
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "wms_erp"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Security Settings
    SECRET_KEY: str = "enterprise_secret_key_change_me"
    SESSION_TIMEOUT_MINUTES: int = 60

    # UI Settings
    DEFAULT_LANGUAGE: str = "ar"

    # OCR Settings
    OCR_LANG: str = "ar"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
