import secrets
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "AgentForge"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # Security
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    # Frontend / CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Local execution boundaries
    WORKSPACE_ROOT: str = "repos"
    ENABLE_TERMINAL: bool = False

    # AI Providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    NVIDIA_NIM_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: Optional[str] = None
    OPENROUTER_HTTP_REFERER: Optional[str] = None
    OPENROUTER_X_TITLE: str = "AgentForge"
    GROQ_BASE_URL: Optional[str] = None
    NVIDIA_NIM_BASE_URL: Optional[str] = None
    MISTRAL_API_KEY: Optional[str] = None
    MISTRAL_BASE_URL: Optional[str] = "https://api.mistral.ai/v1"

    # ===================================================================
    # OLLAMA — LOCAL INFERENCE (CPU-optimised for i5-1035G1 / 12 GB RAM)
    # ===================================================================
    # IMPORTANT: Must include /v1 for the OpenAI-compatible chat endpoint
    # Ollama serves /v1/chat/completions — NOT /chat/completions at root
    OLLAMA_BASE_URL: Optional[str] = "http://localhost:11434/v1"

    # Per-task model routing — model names must match `ollama list` exactly
    OLLAMA_CODE_MODEL: str = "qwen2.5-coder:7b"       # coding / bug-fix / review
    OLLAMA_REASONING_MODEL: str = "deepseek-r1:7b"     # architecture / reasoning
    OLLAMA_CHAT_MODEL: str = "qwen2.5:7b"              # general chat
    OLLAMA_FAST_MODEL: str = "gemma3:4b"               # quick UI responses
    OLLAMA_QUICK_MODEL: str = "llama3.2:3b"            # one-liners / short answers
    OLLAMA_FALLBACK_MODEL: str = "qwen2.5:3b"          # emergency fallback (always installed)

    # CPU tuning — tested on i5-1035G1 / 12 GB
    # Keep context small (4096) to avoid page-filing on 12 GB RAM
    OLLAMA_NUM_CTX: int = 4096
    # 6 threads → leaves 2 logical cores free for OS/UI responsiveness
    OLLAMA_NUM_THREAD: int = 6
    # Keep model warm between requests so subsequent messages are fast (<2s TTFT)
    OLLAMA_KEEP_ALIVE: str = "10m"
    # GPU layers — 0 = CPU only (integrated GPU shares system RAM, not worth it)
    OLLAMA_NUM_GPU: int = 0

    # GitHub OAuth
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_OAUTH_REDIRECT_URI: Optional[str] = None

    # Google OAuth
    GOOGLE_OAUTH_CLIENT_ID: Optional[str] = None
    GOOGLE_OAUTH_CLIENT_SECRET: Optional[str] = None
    GOOGLE_OAUTH_REDIRECT_URI: Optional[str] = None

    # Default AI settings
    DEFAULT_AI_PROVIDER: str = "ollama"
    DEFAULT_MODEL: str = "qwen2.5:7b"
    DEFAULT_FAST_MODEL: str = "llama-3.3-70b-versatile"           # Groq fallback
    DEFAULT_GEMINI_MODEL: str = "gemini-1.5-flash"
    DEFAULT_REASONING_MODEL: str = "openai/gpt-4o"                # OpenRouter fallback
    DEFAULT_CODE_MODEL: str = "nvidia/llama-3.1-nemotron-70b-instruct"
    DEFAULT_LOCAL_MODEL: str = "qwen2.5:7b"

    # Feature flags
    ENABLE_INTELLIGENT_ROUTING: bool = True
    ENABLE_PROVIDER_FALLBACK: bool = True
    ENABLE_COST_OPTIMIZATION: bool = True
    CONTEXT_OPTIMIZATION_ENABLED: bool = True

    # Celery (optional)
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Qdrant (optional vector store)
    QDRANT_URL: Optional[str] = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        if not self.SECRET_KEY:
            if self.ENVIRONMENT.lower() in {"development", "test"}:
                self.SECRET_KEY = secrets.token_urlsafe(32)
            else:
                raise ValueError("SECRET_KEY must be configured outside development")
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must contain at least 32 characters")
        if self.CORS_ORIGINS.strip() == "*":
            raise ValueError("CORS_ORIGINS must list explicit origins")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
