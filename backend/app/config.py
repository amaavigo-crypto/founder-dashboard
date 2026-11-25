import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./founders.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_hours: int = 24 * 7
    pull_secret: str = "dev-pull-secret"
    cron_secret: str = ""  # Vercel Cron sends this as 'Authorization: Bearer <CRON_SECRET>'
    timezone: str = "Asia/Kolkata"
    founder_email: str = "founder@example.com"
    founder_password: str = "change-me"


settings = Settings()

# Fail loudly on Vercel instead of running with dev defaults or a database that forgets everything.
if os.getenv("VERCEL"):
    if settings.database_url.startswith("sqlite"):
        raise RuntimeError("Set DATABASE_URL to a Postgres database. SQLite cannot persist on Vercel.")
    if "dev-" in settings.jwt_secret or "dev-" in settings.pull_secret or len(settings.jwt_secret) < 32:
        raise RuntimeError("Set strong JWT_SECRET (32+ characters) and PULL_SECRET in the Vercel project settings.")
