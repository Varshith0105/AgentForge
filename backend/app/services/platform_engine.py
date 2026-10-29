# pyright: reportMissingTypeStubs=false

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Iterable, Optional, Sequence

import httpx

from app.core.config import settings


SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "__pycache__",
    ".next",
    ".turbo",
    ".mypy_cache",
    ".pytest_cache",
}

TEXT_EXTENSIONS = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".json": "json",
    ".md": "markdown",
    ".txt": "text",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sql": "sql",
}


@dataclass(frozen=True)
class ProviderSelection:
    provider: str
    model: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None


# ─────────────────────────────────────────────────────────────
# Ollama model availability cache
# Avoids hitting /api/tags on every single request
# ─────────────────────────────────────────────────────────────
_ollama_models_cache: list[str] = []
_ollama_cache_ts: float = 0.0
_OLLAMA_CACHE_TTL: float = 30.0  # seconds


async def _get_ollama_models() -> list[str]:
    """Return list of installed Ollama model names, cached for 30 s."""
    global _ollama_models_cache, _ollama_cache_ts
    now = time.perf_counter()
    if _ollama_models_cache and (now - _ollama_cache_ts) < _OLLAMA_CACHE_TTL:
        return _ollama_models_cache
    base = (settings.OLLAMA_BASE_URL or "http://localhost:11434/v1").rstrip("/")
    # /api/tags lives at root, not under /v1
    tags_url = base.replace("/v1", "").rstrip("/") + "/api/tags"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(tags_url)
            if resp.status_code == 200:
                data = resp.json()
                _ollama_models_cache = [m["name"] for m in data.get("models", [])]
                _ollama_cache_ts = now
                return _ollama_models_cache
    except Exception:
        pass
    return []


def _best_ollama_model(task_type: Optional[str], installed: list[str]) -> str:
    """
    Pick the most appropriate installed Ollama model for the given task.
    Falls back through the preference list until one is installed.
    Returns the first installed fallback if nothing matches.
    """
    task = (task_type or "chat").lower()

    # Ordered preference lists per task category
    if task in {"coding", "code", "bug", "review", "refactor", "sqlalchemy", "react"}:
        preferences = [
            settings.OLLAMA_CODE_MODEL,       # qwen2.5-coder:7b
            settings.OLLAMA_CHAT_MODEL,        # qwen2.5:7b
            settings.OLLAMA_QUICK_MODEL,       # llama3.2:3b
            settings.OLLAMA_FALLBACK_MODEL,    # qwen2.5:3b
        ]
    elif task in {"reasoning", "architecture", "design", "analysis"}:
        preferences = [
            settings.OLLAMA_REASONING_MODEL,   # deepseek-r1:7b
            settings.OLLAMA_CHAT_MODEL,        # qwen2.5:7b
            settings.OLLAMA_CODE_MODEL,        # qwen2.5-coder:7b
            settings.OLLAMA_FALLBACK_MODEL,
        ]
    elif task in {"quick", "short", "oneshot"}:
        preferences = [
            settings.OLLAMA_QUICK_MODEL,       # llama3.2:3b
            settings.OLLAMA_FAST_MODEL,        # gemma3:4b
            settings.OLLAMA_FALLBACK_MODEL,
            settings.OLLAMA_CHAT_MODEL,
        ]
    elif task in {"fast", "ui"}:
        preferences = [
            settings.OLLAMA_FAST_MODEL,        # gemma3:4b
            settings.OLLAMA_QUICK_MODEL,       # llama3.2:3b
            settings.OLLAMA_FALLBACK_MODEL,
            settings.OLLAMA_CHAT_MODEL,
        ]
    else:  # chat, general, explain, fastapi, default
        preferences = [
            settings.OLLAMA_CHAT_MODEL,        # qwen2.5:7b
            settings.OLLAMA_CODE_MODEL,        # qwen2.5-coder:7b
            settings.OLLAMA_FAST_MODEL,        # gemma3:4b
            settings.OLLAMA_QUICK_MODEL,       # llama3.2:3b
            settings.OLLAMA_FALLBACK_MODEL,    # qwen2.5:3b
        ]

    installed_set = set(installed)
    for model in preferences:
        if model in installed_set:
            return model
    # Ultimate fallback — any installed model
    return installed[0] if installed else settings.OLLAMA_FALLBACK_MODEL


def _configured(value: Optional[str]) -> bool:
    return bool(value and str(value).strip())


def list_available_providers() -> list[dict[str, Any]]:
    providers: list[dict[str, Any]] = []
    if _configured(settings.OLLAMA_BASE_URL):
        providers.append({"name": "ollama", "available": True, "mode": "openai-compatible"})
    if _configured(settings.GROQ_API_KEY):
        providers.append({"name": "groq", "available": True, "mode": "openai-compatible"})
    if _configured(settings.OPENROUTER_API_KEY):
        providers.append({"name": "openrouter", "available": True, "mode": "openai-compatible"})
    if _configured(settings.NVIDIA_NIM_API_KEY):
        providers.append({"name": "nvidia", "available": True, "mode": "openai-compatible"})
    if _configured(settings.MISTRAL_API_KEY):
        providers.append({"name": "mistral", "available": True, "mode": "openai-compatible"})
    if _configured(settings.OPENAI_API_KEY):
        providers.append({"name": "openai", "available": True, "mode": "openai-compatible"})
    if _configured(settings.GOOGLE_API_KEY):
        providers.append({"name": "google", "available": True, "mode": "gemini"})
    return providers


def _provider_base_url(provider: str) -> Optional[str]:
    provider = provider.lower()
    if provider == "ollama":
        return settings.OLLAMA_BASE_URL or "http://localhost:11434/v1"
    if provider == "groq":
        return settings.GROQ_BASE_URL or "https://api.groq.com/openai/v1"
    if provider == "openrouter":
        return settings.OPENROUTER_BASE_URL or "https://openrouter.ai/api/v1"
    if provider == "nvidia":
        return settings.NVIDIA_NIM_BASE_URL or "https://integrate.api.nvidia.com/v1"
    if provider == "mistral":
        return settings.MISTRAL_BASE_URL or "https://api.mistral.ai/v1"
    if provider == "openai":
        return "https://api.openai.com/v1"
    return None


def _provider_api_key(provider: str) -> Optional[str]:
    provider = provider.lower()
    if provider == "groq":
        return settings.GROQ_API_KEY
    if provider == "openrouter":
        return settings.OPENROUTER_API_KEY
    if provider == "nvidia":
        return settings.NVIDIA_NIM_API_KEY
    if provider == "mistral":
        return settings.MISTRAL_API_KEY
    if provider == "openai":
        return settings.OPENAI_API_KEY
    if provider == "google":
        return settings.GOOGLE_API_KEY
    return None


def _default_provider_candidates(
    prompt_text: str,
    requested_model: Optional[str] = None,
    task_type: Optional[str] = None,
    installed_ollama_models: Optional[list[str]] = None,
) -> list[ProviderSelection]:
    """Build an ordered candidate list with Ollama first."""
    candidates: list[ProviderSelection] = []

    # ─── Priority 1: Ollama (local CPU inference) ─────────────────────────
    if _configured(settings.OLLAMA_BASE_URL):
        if requested_model:
            local_model = requested_model
        elif installed_ollama_models:
            local_model = _best_ollama_model(task_type, installed_ollama_models)
        else:
            local_model = settings.DEFAULT_LOCAL_MODEL
        candidates.append(ProviderSelection(
            provider="ollama",
            model=local_model,
            base_url=_provider_base_url("ollama"),
        ))

    # ─── Priority 2: Groq (fastest cloud, free tier) ─────────────────────
    if _configured(settings.GROQ_API_KEY):
        groq_model = settings.DEFAULT_FAST_MODEL
        if requested_model and "llama" in requested_model.lower():
            groq_model = requested_model
        candidates.append(ProviderSelection(
            provider="groq",
            model=groq_model,
            base_url=_provider_base_url("groq"),
            api_key=settings.GROQ_API_KEY,
        ))

    # ─── Priority 3: OpenRouter ───────────────────────────────────
    if _configured(settings.OPENROUTER_API_KEY):
        candidates.append(ProviderSelection(
            provider="openrouter",
            model=requested_model or settings.DEFAULT_REASONING_MODEL,
            base_url=_provider_base_url("openrouter"),
            api_key=settings.OPENROUTER_API_KEY,
        ))

    # ─── Priority 4: NVIDIA NIM ──────────────────────────────────
    if _configured(settings.NVIDIA_NIM_API_KEY):
        candidates.append(ProviderSelection(
            provider="nvidia",
            model=requested_model or settings.DEFAULT_CODE_MODEL,
            base_url=_provider_base_url("nvidia"),
            api_key=settings.NVIDIA_NIM_API_KEY,
        ))

    # ─── Priority 5: Google Gemini ────────────────────────────────
    if _configured(settings.GOOGLE_API_KEY):
        candidates.append(ProviderSelection(
            provider="google",
            model=requested_model or settings.DEFAULT_GEMINI_MODEL,
            api_key=settings.GOOGLE_API_KEY,
        ))

    # ─── Priority 6: Mistral ─────────────────────────────────────
    if _configured(settings.MISTRAL_API_KEY):
        candidates.append(ProviderSelection(
            provider="mistral",
            model=requested_model or "mistral-small-latest",
            base_url=_provider_base_url("mistral"),
            api_key=settings.MISTRAL_API_KEY,
        ))

    # ─── Priority 7: OpenAI ───────────────────────────────────────
    if _configured(settings.OPENAI_API_KEY):
        candidates.append(ProviderSelection(
            provider="openai",
            model=requested_model or settings.DEFAULT_MODEL,
            base_url=_provider_base_url("openai"),
            api_key=settings.OPENAI_API_KEY,
        ))

    return candidates


async def stream_chat_completion(
    messages: Sequence[dict[str, str]],
    *,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    temperature: float = 0.2,
    task_type: Optional[str] = None,
) -> AsyncIterator[dict[str, Any]]:
    """
    Stream a chat completion from the best available provider.

    Provider priority (when no explicit provider given):
      1. Ollama (local CPU) — uses smart per-task model selection
      2. Groq
      3. OpenRouter
      4. NVIDIA NIM
      5. Google Gemini
      6. Mistral
      7. OpenAI

    Args:
        task_type: hint for model selection — 'coding', 'reasoning', 'chat',
                   'quick', 'fast'. Influences which Ollama model is chosen.
    """
    prompt_text = "\n".join(message.get("content", "") for message in messages)

    # Fetch installed Ollama models once (cached for 30 s)
    installed_ollama = await _get_ollama_models()

    # Build candidate list
    candidates: list[ProviderSelection] = []
    if provider:
        explicit_provider = provider.lower().strip()
        explicit_api_key = _provider_api_key(explicit_provider)
        explicit_base_url = _provider_base_url(explicit_provider)
        # If explicit provider is ollama and no model specified, apply smart routing
        if explicit_provider == "ollama" and not model and installed_ollama:
            explicit_model = _best_ollama_model(task_type, installed_ollama)
        else:
            explicit_model = model or settings.DEFAULT_LOCAL_MODEL
        print(
            f"[AI Router] Explicit provider='{explicit_provider}' | "
            f"model='{explicit_model}' | task='{task_type}' | endpoint='{explicit_base_url}' | "
            f"has_api_key={bool(explicit_api_key)}"
        )
        candidates.append(ProviderSelection(
            provider=explicit_provider,
            model=explicit_model,
            base_url=explicit_base_url,
            api_key=explicit_api_key,
        ))
        # Append full auto-routing list as fallbacks
        for auto in _default_provider_candidates(prompt_text, model, task_type, installed_ollama):
            if auto.provider != explicit_provider:
                candidates.append(auto)
    else:
        candidates = _default_provider_candidates(prompt_text, model, task_type, installed_ollama)
        print(
            f"[AI Router] Auto-routing | task='{task_type}' | "
            f"{len(candidates)} candidates: {[c.provider for c in candidates]}"
        )

    tried_providers: list[str] = []
    for selection in candidates:
        start_time = time.perf_counter()
        print(
            f"[AI Router] Trying provider='{selection.provider}' | "
            f"model='{selection.model}' | endpoint='{selection.base_url}' | "
            f"has_api_key={bool(selection.api_key)}"
        )
        try:
            if selection.provider == "google":
                chunks_yielded = 0
                async for chunk in _stream_gemini(messages, selection.model, temperature):
                    chunks_yielded += 1
                    yield chunk
                elapsed = time.perf_counter() - start_time
                print(f"[AI Router] 'google' OK in {elapsed:.2f}s ({chunks_yielded} chunks)")
                return

            if selection.base_url:
                tokens = 0
                async for chunk in _stream_openai_compatible(messages, selection, temperature):
                    tokens += 1
                    yield chunk
                elapsed = time.perf_counter() - start_time
                # Emit a final metadata sentinel chunk with latency + token count
                yield {
                    "content": "",
                    "provider": selection.provider,
                    "model": selection.model,
                    "is_local": selection.provider == "ollama",
                    "latency_ms": int(elapsed * 1000),
                    "tokens": tokens,
                    "done": True,
                }
                print(
                    f"[AI Router] '{selection.provider}' OK in {elapsed:.2f}s "
                    f"({tokens} chunks | model='{selection.model}')"
                )
                return

            print(f"[AI Router] '{selection.provider}' skipped: no base_url.")
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            print(
                f"[AI Router] '{selection.provider}' FAILED after {elapsed:.2f}s: "
                f"{type(exc).__name__}: {exc}"
            )
            tried_providers.append(f"{selection.provider}({type(exc).__name__})")
            continue

    # ALL providers exhausted
    import asyncio
    tried_str = ", ".join(tried_providers) if tried_providers else "none"
    error_msg = (
        f"**[AgentForge] All LLM providers failed.**\n\n"
        f"Tried: {tried_str}\n\n"
        f"Please check your API keys in `.env` and ensure at least one provider "
        f"(Ollama, Groq, OpenRouter, NVIDIA, or Gemini) is correctly configured."
    )
    print(f"[AI Router] ALL FAILED — tried: {tried_str}")
    words = error_msg.split(" ")
    for i in range(0, len(words), 3):
        chunk_text = " ".join(words[i:i+3]) + " "
        yield {"content": chunk_text, "provider": "agentforge-error", "model": model or "none", "is_local": False}
        await asyncio.sleep(0.01)


async def _stream_openai_compatible(
    messages: Sequence[dict[str, str]],
    selection: ProviderSelection,
    temperature: float,
) -> AsyncIterator[dict[str, Any]]:
    if not selection.base_url:
        raise RuntimeError(f"Base URL for provider '{selection.provider}' is not configured.")

    headers = {"Content-Type": "application/json"}
    if selection.api_key:
        headers["Authorization"] = f"Bearer {selection.api_key}"
    if selection.provider == "openrouter":
        headers["HTTP-Referer"] = settings.OPENROUTER_HTTP_REFERER or "http://localhost"
        headers["X-Title"] = settings.OPENROUTER_X_TITLE or "AgentForge"

    payload: dict[str, Any] = {
        "model": selection.model,
        "messages": list(messages),
        "stream": True,
        "temperature": temperature,
    }

    # Inject Ollama CPU optimisation options
    # These are ignored by cloud providers but critical for local CPU perf
    if selection.provider == "ollama":
        payload["options"] = {
            "num_ctx": settings.OLLAMA_NUM_CTX,       # 4096 — keeps RAM usage low
            "num_thread": settings.OLLAMA_NUM_THREAD,  # 6 of 8 threads
            "num_gpu": settings.OLLAMA_NUM_GPU,        # 0 = CPU only
        }
        payload["keep_alive"] = settings.OLLAMA_KEEP_ALIVE  # keep warm between requests

    # Construct URL — base_url already ends with /v1 for Ollama
    url = f"{selection.base_url.rstrip('/')}/chat/completions"

    # Ollama needs longer connect timeout on first load (cold start up to 30s)
    if selection.provider == "ollama":
        timeout = httpx.Timeout(120.0, connect=15.0)
    else:
        timeout = httpx.Timeout(30.0, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as response:
            print(
                f"[AI Router] HTTP {response.status_code} from '{selection.provider}' "
                f"| url='{url}' | model='{selection.model}'"
            )
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if raw == "[DONE]":
                    break
                try:
                    chunk = json.loads(raw)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield {
                            "content": content,
                            "provider": selection.provider,
                            "model": selection.model,
                            "is_local": selection.provider == "ollama",
                        }
                except json.JSONDecodeError:
                    continue


async def _stream_gemini(
    messages: Sequence[dict[str, str]],
    model: str,
    temperature: float,
) -> AsyncIterator[dict[str, Any]]:
    try:
        from importlib import import_module  # type: ignore[reportMissingTypeStubs]

        genai = import_module("google.generativeai")  # type: ignore[reportMissingTypeStubs]
    except Exception as exc:  # pragma: no cover - import guard
        raise RuntimeError("Gemini provider is not installed.") from exc

    if not _configured(settings.GOOGLE_API_KEY):
        raise RuntimeError("GOOGLE_API_KEY is not configured.")

    genai.configure(api_key=settings.GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel(model)
    prompt = _messages_to_prompt(messages)

    response = gemini_model.generate_content(
        prompt,
        stream=True,
        generation_config={"temperature": temperature},
    )
    for chunk in response:
        text = getattr(chunk, "text", None)
        if text:
            yield {"content": text, "provider": "google", "model": model}


def _messages_to_prompt(messages: Sequence[dict[str, str]]) -> str:
    lines: list[str] = []
    for message in messages:
        role = message.get("role", "user").upper()
        content = message.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n\n".join(lines)


def estimate_tokens(text: str) -> int:
    if not text.strip():
        return 0
    return max(1, int(len(text.split()) * 1.35))


def estimate_cost(provider: str, model: Optional[str], prompt_tokens: int, completion_tokens: int) -> float:
    token_total = prompt_tokens + completion_tokens
    provider = provider.lower()
    if provider in {"groq", "ollama"}:
        return 0.0
    if provider == "google":
        return round(token_total * 0.0000035, 6)
    if provider == "openrouter":
        return round(token_total * 0.0000055, 6)
    if provider == "nvidia":
        return round(token_total * 0.0000045, 6)
    return round(token_total * 0.000005, 6)


def repository_files(repo_path: str, *, limit: int = 5000) -> list[dict[str, Any]]:
    root = Path(repo_path)
    if not root.exists():
        return []

    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if len(files) >= limit:
            break
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        suffix = path.suffix.lower()
        files.append(
            {
                "name": path.name,
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "language": TEXT_EXTENSIONS.get(suffix, suffix.lstrip(".") or "plaintext"),
                "size": stat.st_size,
                "modified_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(stat.st_mtime)),
            }
        )
    return files


def repository_stats(repo_path: str) -> dict[str, Any]:
    root = Path(repo_path)
    if not root.exists():
        return {
            "total_files": 0,
            "total_lines": 0,
            "total_functions": 0,
            "total_classes": 0,
            "total_imports": 0,
            "language_counts": {},
            "largest_files": [],
        }

    total_files = 0
    total_lines = 0
    total_functions = 0
    total_classes = 0
    total_imports = 0
    language_counts: dict[str, int] = {}
    largest_files: list[dict[str, Any]] = []

    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        suffix = path.suffix.lower()
        language = TEXT_EXTENSIONS.get(suffix, suffix.lstrip(".") or "plaintext")
        language_counts[language] = language_counts.get(language, 0) + 1
        total_files += 1

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        total_lines += text.count("\n") + (1 if text else 0)
        if suffix == ".py":
            py_stats = _python_file_stats(text)
            total_functions += py_stats["functions"]
            total_classes += py_stats["classes"]
            total_imports += py_stats["imports"]
        else:
            total_imports += _generic_import_count(text)
            total_functions += _generic_function_count(text)
            total_classes += _generic_class_count(text)

        largest_files.append({"path": str(path.relative_to(root)).replace("\\", "/"), "size": len(text)})

    largest_files = sorted(largest_files, key=lambda item: item["size"], reverse=True)[:10]

    return {
        "total_files": total_files,
        "total_lines": total_lines,
        "total_functions": total_functions,
        "total_classes": total_classes,
        "total_imports": total_imports,
        "language_counts": dict(sorted(language_counts.items(), key=lambda item: item[1], reverse=True)),
        "largest_files": largest_files,
    }


def build_knowledge_graph(repo_path: str) -> dict[str, Any]:
    root = Path(repo_path)
    if not root.exists():
        return {"nodes": [], "edges": [], "stats": repository_stats(repo_path)}

    stats = repository_stats(repo_path)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        rel_path = str(path.relative_to(root)).replace("\\", "/")
        file_id = f"file:{rel_path}"
        nodes.append({"id": file_id, "label": path.name, "type": "file", "path": rel_path})
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if path.suffix.lower() == ".py":
            tree = _safe_python_ast(text)
            if tree is not None:
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_id = f"class:{rel_path}:{node.name}"
                        nodes.append({"id": class_id, "label": node.name, "type": "class", "path": rel_path})
                        edges.append({"source": file_id, "target": class_id, "relationship": "contains"})
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_id = f"function:{rel_path}:{node.name}"
                        nodes.append({"id": func_id, "label": node.name, "type": "function", "path": rel_path})
                        edges.append({"source": file_id, "target": func_id, "relationship": "contains"})
                for imported in _python_imports(tree):
                    module_id = f"module:{imported}"
                    nodes.append({"id": module_id, "label": imported, "type": "module"})
                    edges.append({"source": file_id, "target": module_id, "relationship": "imports"})
        else:
            for imported in _generic_imports(text):
                module_id = f"module:{imported}"
                nodes.append({"id": module_id, "label": imported, "type": "module"})
                edges.append({"source": file_id, "target": module_id, "relationship": "imports"})

    return {"nodes": _dedupe_nodes(nodes), "edges": _dedupe_edges(edges), "stats": stats}


def repository_memory(repo_path: str) -> dict[str, Any]:
    stats = repository_stats(repo_path)
    graph = build_knowledge_graph(repo_path)
    top_languages = list(stats.get("language_counts", {}).items())[:5]
    top_files = [item["path"] for item in stats.get("largest_files", [])[:5]]

    memories = [
        {
            "title": "Repository shape",
            "content": f"{stats['total_files']} files, {stats['total_lines']} lines, {stats['total_functions']} functions, {stats['total_classes']} classes.",
            "category": "architecture",
        },
        {
            "title": "Dominant languages",
            "content": ", ".join(f"{language} ({count})" for language, count in top_languages) or "No source files discovered.",
            "category": "analysis",
        },
        {
            "title": "Largest files",
            "content": ", ".join(top_files) or "No files discovered.",
            "category": "hotspots",
        },
        {
            "title": "Graph density",
            "content": f"{len(graph['nodes'])} nodes and {len(graph['edges'])} edges discovered from imports and declarations.",
            "category": "knowledge",
        },
    ]

    return {
        "memories": memories,
        "context_summary": " | ".join(memory["content"] for memory in memories),
        "vector_count": len(graph["nodes"]),
    }


def search_repository(repo_path: str, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
    root = Path(repo_path)
    if not root.exists():
        return []

    normalized_query = _normalize_text(query)
    if not normalized_query:
        return []

    results: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        haystack = _normalize_text(f"{path.name}\n{text}")
        score = _score_text_match(normalized_query, haystack)
        if score <= 0:
            continue

        results.append(
            {
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "name": path.name,
                "score": score,
                "snippet": _extract_snippet(text, query),
                "language": TEXT_EXTENSIONS.get(path.suffix.lower(), path.suffix.lstrip(".") or "plaintext"),
            }
        )

    results.sort(key=lambda item: (item["score"], -len(item.get("snippet", ""))), reverse=True)
    return results[:limit]


def git_status(repo_path: Optional[str]) -> dict[str, Any]:
    repo = _normalize_repo_path(repo_path)
    if not repo:
        return {"changes": [], "branch": None, "ahead": 0, "behind": 0}

    short_status = _run_git(["status", "--short"], repo)
    branch = _run_git(["branch", "--show-current"], repo)
    changes: list[dict[str, str]] = []
    for line in short_status["stdout"].splitlines():
        if not line.strip():
            continue
        status_code = line[:2].strip() or "M"
        file_path = line[3:].strip()
        changes.append({"status": status_code, "file": file_path})

    ahead, behind = _branch_divergence(repo)
    return {"changes": changes, "branch": branch["stdout"] or None, "ahead": ahead, "behind": behind}


def git_branches(repo_path: Optional[str]) -> list[str]:
    repo = _normalize_repo_path(repo_path)
    if not repo:
        return []
    result = _run_git(["branch", "-a"], repo)
    branches = []
    for line in result["stdout"].splitlines():
        cleaned = line.strip().lstrip("* ").strip()
        if cleaned:
            branches.append(cleaned)
    return branches


def git_log(repo_path: Optional[str], limit: int = 20) -> list[dict[str, Any]]:
    repo = _normalize_repo_path(repo_path)
    if not repo:
        return []
    fmt = "--pretty=format:%H|%an|%ae|%ad|%s"
    result = _run_git(["log", fmt, f"-{limit}", "--date=iso"], repo)
    commits: list[dict[str, Any]] = []
    for line in result["stdout"].splitlines():
        if "|" not in line:
            continue
        parts = line.split("|", 4)
        if len(parts) != 5:
            continue
        commits.append(
            {
                "hash": parts[0],
                "author": parts[1],
                "email": parts[2],
                "date": parts[3],
                "message": parts[4],
            }
        )
    return commits


def git_commit(repo_path: Optional[str], message: str) -> dict[str, Any]:
    repo = _normalize_repo_path(repo_path)
    if not repo:
        raise RuntimeError("Repository path is required for git commits.")
    add_result = _run_git(["add", "-A"], repo)
    if add_result["returncode"] != 0:
        raise RuntimeError(add_result["stderr"] or "git add failed")
    result = _run_git(["commit", "-m", message], repo)
    if result["returncode"] != 0:
        raise RuntimeError(result["stderr"] or "git commit failed")
    return result


def _normalize_repo_path(repo_path: Optional[str]) -> Optional[str]:
    if not repo_path:
        return None
    candidate = Path(repo_path)
    return str(candidate) if candidate.exists() else None


def _run_git(args: list[str], cwd: str) -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=60,
            check=False,
        )
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except FileNotFoundError as exc:
        return {"stdout": "", "stderr": str(exc), "returncode": -1}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "git command timed out", "returncode": -1}


def _branch_divergence(repo_path: str) -> tuple[int, int]:
    result = _run_git(["rev-list", "--left-right", "--count", "HEAD...@{u}"], repo_path)
    if result["returncode"] != 0 or not result["stdout"]:
        return 0, 0
    parts = result["stdout"].split()
    if len(parts) != 2:
        return 0, 0
    return int(parts[0]), int(parts[1])


def _safe_python_ast(text: str) -> Optional[ast.AST]:
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def _python_file_stats(text: str) -> dict[str, int]:
    tree = _safe_python_ast(text)
    if tree is None:
        return {"functions": 0, "classes": 0, "imports": 0}
    functions = 0
    classes = 0
    imports = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
        elif isinstance(node, ast.ClassDef):
            classes += 1
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            imports += 1
    return {"functions": functions, "classes": classes, "imports": imports}


def _python_imports(tree: ast.AST) -> list[str]:
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module:
                imports.append(module)
    return imports


def _generic_imports(text: str) -> list[str]:
    return sorted(set(_generic_import_pattern(text)))


def _generic_import_pattern(text: str) -> list[str]:
    matches: list[str] = []
    patterns = [
        r"import\s+(?:[^'\";]+?from\s+)?['\"]([^'\"]+)['\"]",
        r"from\s+['\"]([^'\"]+)['\"]\s+import",
    ]
    for pattern in patterns:
        matches.extend(re.findall(pattern, text, flags=re.MULTILINE))
    return matches


def _generic_import_count(text: str) -> int:
    return len(_generic_import_pattern(text))


def _generic_function_count(text: str) -> int:
    return len(re.findall(r"\bfunction\s+[A-Za-z_][A-Za-z0-9_]*\b|=>", text))


def _generic_class_count(text: str) -> int:
    return len(re.findall(r"\bclass\s+[A-Za-z_][A-Za-z0-9_]*\b", text))


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _score_text_match(query: str, text: str) -> int:
    query_tokens = [token for token in _normalize_text(query).split(" ") if token]
    if not query_tokens:
        return 0
    score = 0
    for token in query_tokens:
        if token in text:
            score += 3
        score += text.count(token)
    return score


def _extract_snippet(text: str, query: str, window: int = 120) -> str:
    if not text:
        return ""
    normalized_query = _normalize_text(query)
    match_index = _normalize_text(text).find(normalized_query)
    if match_index < 0:
        return text[:window].strip()
    start = max(0, match_index - window // 2)
    end = min(len(text), match_index + len(query) + window // 2)
    return text[start:end].strip()


def _dedupe_nodes(nodes: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for node in nodes:
        node_id = node.get("id")
        if not node_id or node_id in seen:
            continue
        seen.add(node_id)
        unique.append(node)
    return unique


def _dedupe_edges(edges: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict[str, Any]] = []
    for edge in edges:
        key = (str(edge.get("source")), str(edge.get("target")), str(edge.get("relationship")))
        if key in seen:
            continue
        seen.add(key)
        unique.append(edge)
    return unique


def repository_stats(repo_path: str) -> dict[str, Any]:
    """Collect statistics about a repository: LOC, function/class counts, language distribution."""
    total_files = 0
    total_lines = 0
    total_functions = 0
    total_classes = 0
    language_counts: dict[str, int] = {}
    language_lines: dict[str, int] = {}
    file_sizes: list[tuple[int, str]] = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            fpath = os.path.join(root, fname)
            ext = Path(fname).suffix.lower()
            lang = TEXT_EXTENSIONS.get(ext)
            if lang is None:
                continue
            total_files += 1
            language_counts[lang] = language_counts.get(lang, 0) + 1
            try:
                content = Path(fpath).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            lines = content.count("\n") + 1
            total_lines += lines
            language_lines[lang] = language_lines.get(lang, 0) + lines
            file_sizes.append((lines, os.path.relpath(fpath, repo_path).replace("\\", "/")))
            if ext == ".py":
                try:
                    tree = ast.parse(content)
                    total_functions += sum(
                        1 for node in ast.walk(tree)
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    )
                    total_classes += sum(
                        1 for node in ast.walk(tree)
                        if isinstance(node, ast.ClassDef)
                    )
                except Exception:
                    pass

    file_sizes.sort(reverse=True)
    largest = [{"lines": s, "path": p} for s, p in file_sizes[:10]]
    return {
        "total_files": total_files,
        "total_lines": total_lines,
        "total_functions": total_functions,
        "total_classes": total_classes,
        "language_counts": language_counts,
        "language_lines": language_lines,
        "largest_files": largest,
    }

