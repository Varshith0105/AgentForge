from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from typing import Any
from sqlalchemy import update

from app.api import deps
from app.core.database import get_db
from app.models.user import User

router = APIRouter()


class AIConfig(BaseModel):
    provider: Optional[str] = "openai"
    model: Optional[str] = "gpt-4o"
    theme: Optional[str] = "vs-dark"
    font_size: Optional[int] = 14


DEFAULT_CONFIG = {
    "provider": "auto",
    "model": "auto",
    "theme": "vs-dark",
    "font_size": 14,
}

_user_configs: dict[str, dict[str, object]] = {}


@router.get("/config")
def get_config(current_user: User = Depends(deps.get_current_user), db: Session = Depends(get_db)):
    """Get user's AI configuration including provider status."""
    from app.core.config import settings
    preferences_json = getattr(current_user, "preferences_json", None)
    preferences: dict[str, Any] = {}
    if isinstance(preferences_json, dict):
        preferences.update(preferences_json)
    config = preferences.get("ai_os", {})
    return {
        **DEFAULT_CONFIG,
        **config,
        # Provider configuration status
        "ollama_configured": bool(settings.OLLAMA_BASE_URL),
        "groq_configured": bool(settings.GROQ_API_KEY),
        "openrouter_configured": bool(settings.OPENROUTER_API_KEY),
        "nvidia_configured": bool(settings.NVIDIA_NIM_API_KEY),
        "google_configured": bool(settings.GOOGLE_API_KEY),
        "openai_configured": bool(settings.OPENAI_API_KEY),
    }


@router.put("/config")
def update_config(config: AIConfig, current_user: User = Depends(deps.get_current_user), db: Session = Depends(get_db)):
    """Update user's AI configuration."""
    preferences_json = getattr(current_user, "preferences_json", None)
    preferences: dict[str, Any] = {}
    if isinstance(preferences_json, dict):
        preferences.update(preferences_json)
    preferences["ai_os"] = config.model_dump()
    db.execute(update(User).where(User.id == current_user.id).values(preferences_json=preferences))
    db.commit()
    return {"message": "Configuration saved", "config": {**DEFAULT_CONFIG, **config.model_dump()}}


@router.get("/info")
def get_info(current_user: User = Depends(deps.get_current_user)):
    from app.core.ai import get_ai_orchestrator, get_provider_manager
    from app.core.config import settings
    try:
        orchestrator = get_ai_orchestrator()
        provider_manager = get_provider_manager()
        return {
            "status": "operational",
            "models": orchestrator.model_registry.list_models(),
            "prompt_templates": orchestrator.prompt_manager.list_templates(),
            "providers": provider_manager.list_providers(),
            "configured_providers": {
                "openai": bool(settings.OPENAI_API_KEY),
                "anthropic": bool(settings.ANTHROPIC_API_KEY),
                "google": bool(settings.GOOGLE_API_KEY),
                "groq": bool(settings.GROQ_API_KEY),
                "openrouter": bool(settings.OPENROUTER_API_KEY),
                "nvidia": bool(settings.NVIDIA_NIM_API_KEY),
                "ollama": bool(settings.OLLAMA_BASE_URL),
            },
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/models")
def list_models(current_user: User = Depends(deps.get_current_user)):
    from app.core.ai import get_ai_orchestrator
    try:
        orchestrator = get_ai_orchestrator()
        return {"models": orchestrator.model_registry.list_models()}
    except Exception as e:
        return {"models": [], "error": str(e)}


@router.get("/providers")
def list_providers(current_user: User = Depends(deps.get_current_user)):
    from app.core.ai import get_provider_manager
    from app.core.config import settings
    try:
        provider_manager = get_provider_manager()
        return {
            "providers": provider_manager.list_providers(),
            "configured": {
                "openai": bool(settings.OPENAI_API_KEY),
                "anthropic": bool(settings.ANTHROPIC_API_KEY),
                "google": bool(settings.GOOGLE_API_KEY),
                "groq": bool(settings.GROQ_API_KEY),
                "openrouter": bool(settings.OPENROUTER_API_KEY),
                "nvidia": bool(settings.NVIDIA_NIM_API_KEY),
                "ollama": bool(settings.OLLAMA_BASE_URL),
            }
        }
    except Exception as e:
        return {"providers": [], "error": str(e)}
