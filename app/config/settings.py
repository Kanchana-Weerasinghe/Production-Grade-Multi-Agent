# app/config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Existing keys
    GROQ_API_KEY: str
    DATABASE_URL: str = "localhost:6379"
    LOG_LEVEL: str = "INFO"

    # Neo4j
    NEO4J_URI: str = ""
    NEO4J_USERNAME: str = ""
    NEO4J_PASSWORD: str = ""

    # HuggingFace
    HUGGINGFACEHUB_API_TOKEN: str = ""

    # LangSmith Observability
    LANGSMITH_TRACING: bool = False
    LANGSMITH_ENDPOINT: str = ""
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = ""

    # Search API
    TAVILY_API_KEY: str = ""

    # Grafana OTEL (Strands/OTEL observability)
    GRAFANA_OTEL_ENDPOINT: str = ""
    GRAFANA_OTEL_HEADERS: str = ""

    # Authentication & Authorization
    AUTH_SECRET_KEY: str = "your-secret-key-change-in-production"
    TOKEN_EXPIRATION_HOURS: int = 24
    RATE_LIMITING_ENABLED: bool = False
    AUTH_ENABLED: bool = True

    # Security Features
    ENABLE_ZERO_TRUST: bool = True
    ENABLE_PROMPT_INJECTION_PROTECTION: bool = True
    ENABLE_JIT_PRIVILEGES: bool = True
    ENABLE_AGENT_IDENTITIES: bool = True
    JIT_TOKEN_LIFETIME_SECONDS: int = 300
    MAX_JIT_TOKENS: int = 100
    JIT_SECRET_KEY: str = "default-jit-secret-change-in-production"

    model_config = SettingsConfigDict(
        env_file=(
            "app/config/env/.env.dev",
            "app/config/secrets/.env.secrets"
        ),
        extra="ignore"
    )

# Global instance
settings = Settings()
