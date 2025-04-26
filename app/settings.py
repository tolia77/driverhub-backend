from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

class DatabaseConfig(BaseConfig):
    database_connection_string: str


class Settings(BaseSettings):
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)


settings = Settings()