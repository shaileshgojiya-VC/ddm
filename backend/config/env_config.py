"""This module contains configuration information."""

from functools import lru_cache
from os.path import join

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

from .project_path import BASE_DIR

# Load .env file
dotenv_path = join(BASE_DIR, ".env")
load_dotenv(dotenv_path)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    DATABASE_URL: str
    DATABASE_NAME: str | None = None
    DATABASE_USER: str | None = None
    DATABASE_PASSWORD: str | None = None
    DATABASE_HOST: str | None = None
    DATABASE_PORT: str | None = None

    # Server Configuration
    SERVER_HOST: str | None = None
    SERVER_PORT: int | None = None

    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # AWS Configuration
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_S3_BUCKET: str
    AWS_S3_BUCKET_NAME: str | None = None
    AWS_BASE_URL: str | None = None

    # Azure Configuration
    AZURE_STORAGE_CONNECTION_STRING: str | None = None
    AZURE_CONTAINER_NAME: str | None = None
    AZURE_STORAGE_ACCOUNT_NAME: str | None = None
    AZURE_STORAGE_ACCOUNT_KEY: str | None = None

    # Application Configuration
    SECRET_KEY: str
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Email Configuration
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_USE_TLS: bool = True
    EMAIL_USERNAME: str | None = None
    FROM_EMAIL: str  # Verified sender email address (required for AWS SES)

    # Session
    SESSION_SECRET_KEY: str = ""

    # Outlook/Microsoft Graph Configuration
    LOGIN_URL: str
    TENANT_ID: str | None = None
    CLIENT_ID: str | None = None
    CLIENT_SECRET: str | None = None
    OUTLOOK_WEBHOOK_URL: str | None = None
    OUTLOOK_API_TOKEN: str | None = None

    # Azure Blob Storage Configuration
    AZURE_STORAGE_CONNECTION_STRING: str | None = None
    AZURE_CONTAINER_NAME: str = "danadairy"
    AZURE_STORAGE_ACCOUNT_NAME: str | None = None
    AZURE_STORAGE_ACCOUNT_KEY: str | None = None
    AZURE_BLOB_STORAGE_URL: str | None = None

    # Bitrix Configuration
    BITRIX_PRODUCT_ROWS_URL: str | None = None
    BITRIX_TOKEN: str | None = None
    BITRIX_URL: str | None = None
    BITRIX_WEBHOOK_URL: str | None = None
    BITRIX_PORTAL_URL: str | None = None

    # Bitrix OAuth Configuration (for file downloads)
    # Option 1: Direct access token (simplest)
    BITRIX_ACCESS_TOKEN: str | None = None

    # Option 2: OAuth credentials for token refresh
    BITRIX_OAUTH_CLIENT_ID: str | None = None
    BITRIX_OAUTH_CLIENT_SECRET: str | None = None
    BITRIX_OAUTH_REFRESH_TOKEN: str | None = None

    # Bitrix Session Cookies (legacy, for backward compatibility)
    USER_LANG: str | None = None
    BITRIX_SM_UIDL: str | None = None
    BITRIX_SM_SALE_UID: str | None = None
    BITRIX_SM_TZ: str | None = None
    BITRIX_SM_PK: str | None = None
    BITRIX_SM_UIDH: str | None = None
    BITRIX_SM_CC: str | None = None
    BITRIX_SM_kernel: str | None = None
    BITRIX_SM_DTOKEN: str | None = None
    BITRIX_SM_SOUND_LOGIN_PLAYED: str | None = None
    qmb: str | None = None
    BITRIX_SM_kernel_0: str | None = None
    PHPSESSID: str | None = None
    BITRIX_PORTAL_URL: str | None = None
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables not defined in the model
    )
    DATABASE_SSL_CA: str | None = None
    DATABASE_SSL_VERIFY: bool = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
