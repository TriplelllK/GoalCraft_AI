from __future__ import annotations

import os


class _Settings:
    """Simple settings object populated from environment variables."""

    @property
    def app_title(self) -> str:
        return os.getenv("APP_TITLE", "GoalCraft AI")

    @property
    def app_version(self) -> str:
        return os.getenv("APP_VERSION", "1.0.0")

    @property
    def cors_origins(self) -> list[str]:
        raw = os.getenv("CORS_ORIGINS", "*")
        return [o.strip() for o in raw.split(",")]

    # ── Storage ──────────────────────────────────────────────────────

    @property
    def storage_backend(self) -> str:
        explicit = os.getenv("STORAGE_BACKEND")
        if explicit:
            return explicit
        # Auto-detect: if POSTGRES_HOST is set we assume postgres
        if os.getenv("POSTGRES_HOST"):
            return "postgres"
        return "memory"

    @property
    def database_url(self) -> str:
        url = os.getenv("DATABASE_URL")
        if url:
            return url
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "hr_goal_ai")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"

    @property
    def postgres_auto_init(self) -> bool:
        return os.getenv("POSTGRES_AUTO_INIT", "true").lower() in ("1", "true", "yes")

    # ── Vector ───────────────────────────────────────────────────────

    @property
    def vector_backend(self) -> str:
        explicit = os.getenv("VECTOR_BACKEND")
        if explicit:
            return explicit
        if os.getenv("QDRANT_URL"):
            return "qdrant"
        return "memory"

    @property
    def qdrant_url(self) -> str:
        return os.getenv("QDRANT_URL", "")

    @property
    def qdrant_api_key(self) -> str:
        return os.getenv("QDRANT_API_KEY", "")

    @property
    def vector_collection(self) -> str:
        return os.getenv("VECTOR_COLLECTION", "hr_goals")

    @property
    def vector_size(self) -> int:
        return int(os.getenv("VECTOR_SIZE", "256"))

    # ── LLM ──────────────────────────────────────────────────────────

    @property
    def openai_api_key(self) -> str:
        return os.getenv("OPENAI_API_KEY", "")

    @property
    def openai_model(self) -> str:
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    @property
    def llm_enabled(self) -> bool:
        """LLM is enabled when an API key is provided."""
        return bool(self.openai_api_key)


settings = _Settings()
