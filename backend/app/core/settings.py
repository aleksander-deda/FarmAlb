from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────────────────────────────
    app_name: str = "FarmAlb"
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = "change-me"
    app_base_url: str = "http://localhost:8000"

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./farma_alb.db"

    # ── Auth ─────────────────────────────────────────────────────────────────
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    # ── Payments ─────────────────────────────────────────────────────────────
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # ── Storage ──────────────────────────────────────────────────────────────
    storage_provider: str = "local"
    storage_local_path: str = "./media"
    cloudflare_r2_bucket: str = ""
    cloudflare_r2_access_key: str = ""
    cloudflare_r2_secret_key: str = ""
    cloudflare_r2_endpoint: str = ""

    # ── Email ────────────────────────────────────────────────────────────────
    email_provider: str = "console"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@farmaalb.al"

    # ── Platform business rules ───────────────────────────────────────────────
    platform_booking_commission_rate: float = 0.10
    platform_order_commission_rate: float = 0.08
    platform_default_currency: str = "ALL" # EUR

    # ── Computed helpers ──────────────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance — call get_settings() anywhere,
    always returns the same object. Cache is reset in tests via
    get_settings.cache_clear().
    """
    return Settings()


settings = get_settings()
