"""Application configuration."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Nodes"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_path: Path = Path("data/nodes.db")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS (for frontend dev server in debug mode, production should set explicitly)
    cors_origins: list[str] = []

    # Author settings
    default_author: str = "Anonymous"

    # Auth settings
    auth_enabled: bool = False
    auth_secret_key: str = ""
    auth_algorithm: str = "HS256"
    auth_access_token_expire_minutes: int = 15
    auth_refresh_token_expire_days: int = 7

    # OIDC SSO settings (generic)
    sso_provider: str = "duo"
    sso_client_id: str = ""
    sso_client_secret: str = ""
    sso_base_url: str = ""
    sso_redirect_uri: str = ""

    # Duo-specific (legacy support, mapped to generic settings)
    duo_client_id: str = ""
    duo_client_secret: str = ""
    duo_api_host: str = ""
    duo_redirect_uri: str = ""

    # Default role for new users (after first admin)
    default_user_role: str = "analyst"

    # Rate limiting
    rate_limit_auth: str = "5/minute"
    rate_limit_api: str = "100/minute"

    # Audit log settings
    audit_log_enabled: bool = True
    audit_log_retention_days: int = 90  # 0 = keep forever
    audit_log_max_size_mb: int = 500

    # SSO failure handling
    sso_fallback_mode: str = "require_sso"  # or "fallback_anonymous"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="NODES_",
        extra="ignore"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-disable audit logging if auth is disabled
        if not self.auth_enabled:
            self.audit_log_enabled = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            if not v:
                return []
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v or []

    @property
    def effective_sso_client_id(self) -> str:
        """Return SSO client ID, falling back to Duo-specific setting."""
        return self.sso_client_id or self.duo_client_id

    @property
    def effective_sso_client_secret(self) -> str:
        """Return SSO client secret, falling back to Duo-specific setting."""
        return self.sso_client_secret or self.duo_client_secret

    @property
    def effective_sso_base_url(self) -> str:
        """Return SSO base URL, constructing from Duo host if needed."""
        if self.sso_base_url:
            return self.sso_base_url
        if self.duo_api_host:
            return f"https://{self.duo_api_host}"
        return ""

    @property
    def effective_cors_origins(self) -> list[str]:
        """Return CORS origins, using localhost in debug mode if none specified."""
        if self.cors_origins:
            return self.cors_origins
        if self.debug:
            return ["http://localhost:5173", "http://localhost:8000"]
        return []


settings = Settings()
