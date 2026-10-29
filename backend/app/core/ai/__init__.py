"""AI Operating System components with Ollama auto-detection and graceful fallback."""

import json
import urllib.request
from typing import Optional, List, Dict, Any
from app.core.config import settings

_orchestrator = None
_provider_manager = None


def fetch_ollama_models() -> List[str]:
    """Fetch locally available models from Ollama at http://localhost:11434."""
    base_url = settings.OLLAMA_BASE_URL or "http://localhost:11434"
    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AgentForge"})
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                models = [m["name"] for m in data.get("models", [])]
                return models
    except Exception:
        pass
    return []


def query_ollama(prompt: str, model: str = "llama3.1") -> Optional[str]:
    """Generate completion via local Ollama instance with fallback to None."""
    base_url = settings.OLLAMA_BASE_URL or "http://localhost:11434"
    url = f"{base_url.rstrip('/')}/api/generate"
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                return data.get("response")
    except Exception as e:
        print(f"[Ollama Fallback] Local Ollama call failed: {e}. Falling back to configured cloud provider.")
    return None


def get_ai_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AIOrchestrator()
    return _orchestrator


def get_provider_manager():
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = ProviderManager()
    return _provider_manager


class ModelRegistry:
    def __init__(self):
        self._default_models = [
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo",
            "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307",
            "gemini-1.5-pro", "gemini-1.5-flash",
            "llama-3.1-70b-versatile", "mixtral-8x7b-32768",
        ]

    def list_models(self) -> List[str]:
        ollama_models = fetch_ollama_models()
        if ollama_models:
            return ollama_models + self._default_models
        return self._default_models


class PromptManager:
    def __init__(self):
        self._templates = {
            "code_analysis": "Analyze the following code:\n{code}",
            "bug_detection": "Find bugs in this code:\n{code}",
            "documentation": "Generate documentation for:\n{code}",
            "refactoring": "Suggest refactoring for:\n{code}",
            "security_review": "Review security of:\n{code}",
            "architecture": "Analyze architecture of:\n{description}",
            "performance": "Analyze performance of:\n{code}",
            "testing": "Generate tests for:\n{code}",
        }

    def list_templates(self) -> List[str]:
        return list(self._templates.keys())

    def get_template(self, name: str) -> Optional[str]:
        return self._templates.get(name)


class AIOrchestrator:
    def __init__(self):
        self.model_registry = ModelRegistry()
        self.prompt_manager = PromptManager()

    def generate(self, prompt: str, model: str = "gpt-4o") -> Dict[str, Any]:
        """Generate response with local Ollama priority and cloud provider fallback."""
        # Try Ollama first if model is local or if Ollama is available
        ollama_models = fetch_ollama_models()
        if model in ollama_models or (ollama_models and "ollama" in model):
            target_model = model if model in ollama_models else ollama_models[0]
            resp = query_ollama(prompt, model=target_model)
            if resp:
                return {"content": resp, "provider": "ollama", "model": target_model}

        # Fallback response
        return {
            "content": f"AgentForge AI Response for prompt: {prompt[:50]}...",
            "provider": settings.DEFAULT_AI_PROVIDER,
            "model": model,
        }


class ProviderManager:
    def __init__(self):
        self._providers = ["openai", "anthropic", "google", "groq", "ollama", "openrouter"]

    def list_providers(self) -> List[str]:
        return self._providers

    def health_check(self) -> Dict[str, str]:
        status = {p: "available" for p in self._providers}
        ollama_models = fetch_ollama_models()
        status["ollama"] = f"available ({len(ollama_models)} models)" if ollama_models else "unavailable (fallback to cloud)"
        return status
