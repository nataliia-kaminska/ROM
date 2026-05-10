from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Research Opportunity Matcher"
    app_env: str = "local"
    debug: bool = False
    database_url: str = "sqlite:///./research_matcher.db"
    redis_url: str = "redis://localhost:6379/0"
    websocket_redis_enabled: bool = False
    websocket_notifications_channel: str = "notifications:realtime"
    elasticsearch_enabled: bool = False
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_opportunity_index: str = "research_opportunities"
    scheduler_tick_seconds: int = 60
    source_sync_interval_seconds: int = 21600
    source_sync_limit: int = 25
    scheduled_grants_gov_keywords: list[str] = ["research", "fellowship"]
    reminder_scan_interval_seconds: int = 3600
    embedding_dimensions: int = 128
    embedding_provider: str = "hash"
    embedding_auto_install: bool = False
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    semantic_candidate_limit: int = 250
    semantic_score_weight: float = 0.35
    eligibility_score_weight: float = 0.35
    deadline_score_weight: float = 0.15
    user_history_score_weight: float = 0.15
    auto_create_tables: bool = True
    cors_origins: list[str] = ["http://127.0.0.1:3000", "http://localhost:3000"]
    log_level: str = "INFO"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    orcid_base_url: str = "https://pub.orcid.org/v3.0"
    openalex_base_url: str = "https://api.openalex.org"
    email_provider: str = "console"
    email_from: str = "Research Matcher <noreply@example.local>"
    frontend_base_url: str = "http://127.0.0.1:3000"
    email_verification_required: bool = True
    email_verification_expire_hours: int = 24
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_api_key: str = ""
    smtp_use_tls: bool = False
    weekly_digest_interval_seconds: int = 604800
    high_match_alert_interval_seconds: int = 3600
    advisor_provider: str = "deterministic"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    advisor_local_base_url: str = "http://localhost:11434/v1"
    advisor_local_model: str = "llama3.1:8b"
    advisor_timeout_seconds: int = 20
    opportunity_extraction_provider: str = "deterministic"
    opportunity_extraction_model: str = ""
    opportunity_extraction_timeout_seconds: int = 20
    profile_enrichment_auto_openalex: bool = False
    profile_enrichment_provider: str = "deterministic"
    profile_enrichment_model: str = ""
    profile_enrichment_max_works: int = 20
    profile_enrichment_timeout_seconds: int = 20

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
