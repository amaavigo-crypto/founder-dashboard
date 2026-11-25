from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./founders.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_hours: int = 24 * 7
    pull_secret: str = "dev-pull-secret"
    timezone: str = "Asia/Kolkata"
    founder_email: str = "founder@example.com"
    founder_password: str = "change-me"


settings = Settings()
