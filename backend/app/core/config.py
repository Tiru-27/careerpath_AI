from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CareerPulse API"
    environment: str = "development"
    database_url: str = "sqlite:///./careerpath.db"
    jwt_secret: str = "change-me-before-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 1440
    cors_origins: str = "http://localhost:8501,http://localhost:3000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_production_secrets(self):
        placeholder_secrets = {"change-me-before-production", "replace-this-with-a-long-random-secret"}
        if self.environment.lower() in {"production", "prod"} and self.jwt_secret in placeholder_secrets:
            raise ValueError("JWT_SECRET must be set to a strong non-placeholder value in production")
        return self


settings = Settings()
