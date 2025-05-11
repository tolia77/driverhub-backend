from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


class DatabaseConfig(BaseConfig):
    database_connection_string: str
    test_database_connection_string: str


class JWTConfig(BaseConfig):
    jwt_secret: str
    jwt_expires_in_minutes: int


class MailgunConfig(BaseConfig):
    mailgun_api_key: str


class AppConfig(BaseConfig):
    environment: str = "production"


class Settings(BaseSettings):
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    jwt: JWTConfig = Field(default_factory=JWTConfig)
    mailgun: MailgunConfig = Field(default_factory=MailgunConfig)
    app: AppConfig = Field(default_factory=AppConfig)


settings = Settings()
