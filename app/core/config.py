from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Research Opportunity Matcher"
    app_env: str = "local"
    debug: bool = False
    database_url: str = "sqlite:///./research_matcher.db"
    redis_url: str = "redis://localhost:6379/0"
    scheduler_tick_seconds: int = 60
    source_sync_interval_seconds: int = 21600
    source_sync_limit: int = 25
    scheduled_grants_gov_keywords: list[str] = ["research", "fellowship"]
    reminder_scan_interval_seconds: int = 3600
    embedding_dimensions: int = 128
    semantic_score_weight: int = 25
    auto_create_tables: bool = True
    cors_origins: list[str] = ["http://127.0.0.1:3000", "http://localhost:3000"]
    log_level: str = "INFO"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    orcid_base_url: str = "https://pub.orcid.org/v3.0"
    openalex_base_url: str = "https://api.openalex.org"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
