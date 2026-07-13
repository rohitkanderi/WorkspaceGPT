"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings sourced from environment variables and `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    openai_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="API key for OpenAI-compatible LLM requests.",
    )
    app_name: str = Field(
        default="WorkspaceGPT",
        description="Public application name.",
    )
    app_version: str = Field(
        default="0.1.0",
        description="Application version exposed by health checks.",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"],
        description="Allowed browser origins for API requests.",
    )
    database_url: str = Field(
        default="sqlite+aiosqlite:///./workspacegpt.db",
        description="SQLAlchemy database URL (SQLite for dev, PostgreSQL for prod).",
    )
    jwt_secret: SecretStr = Field(
        default=SecretStr(""),
        description="Secret used to sign JWT access and refresh tokens.",
    )
    github_token: SecretStr | None = Field(
        default=None,
        description="GitHub personal access token for the GitHub MCP server.",
    )
    workspace_root: Path = Field(
        default=Path("."),
        description="Root directory sandboxed by the filesystem MCP server.",
    )
    mcp_server_config: str = Field(
        default="MCP_SERVER_CONFIG.example.json",
        description="Path to MCP server config JSON or inline JSON string.",
    )

    @field_validator("workspace_root", mode="before")
    @classmethod
    def _coerce_workspace_root(cls, value: str | Path) -> Path:
        """Normalize workspace root to a Path."""
        return Path(value)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _coerce_cors_origins(cls, value: str | list[str]) -> list[str]:
        """Allow comma-separated CORS origins in environment variables."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def resolved_workspace_root(self) -> Path:
        """Return workspace root as an absolute path."""
        root = self.workspace_root
        if root.is_absolute():
            return root.resolve()
        return (_BACKEND_ROOT / root).resolve()

    @property
    def resolved_mcp_server_config(self) -> str:
        """Return MCP config, resolving relative file paths from backend root."""
        raw = self.mcp_server_config.strip()
        if not raw:
            return raw

        path = Path(raw)
        if path.is_file():
            return str(path.resolve())

        candidate = _BACKEND_ROOT / raw
        if candidate.is_file():
            return str(candidate.resolve())

        return raw

    def get_github_token(self) -> str | None:
        """Return the GitHub token as a plain string, if configured."""
        if self.github_token is None:
            return None
        value = self.github_token.get_secret_value().strip()
        return value or None

    def get_openai_api_key(self) -> str:
        """Return the OpenAI API key as a plain string."""
        return self.openai_api_key.get_secret_value().strip()

    def get_jwt_secret(self) -> str:
        """Return the JWT signing secret as a plain string."""
        return self.jwt_secret.get_secret_value().strip()


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
