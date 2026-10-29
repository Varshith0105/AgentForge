import asyncio
import os
import sys
import time
from typing import Optional, Sequence
import httpx

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.services.platform_engine import (
    _provider_base_url,
    _provider_api_key,
    _configured,
)

print("=" * 60)
print("AGENTFORGE PROVIDER DIAGNOSTICS & VERIFICATION")
print("=" * 60)

providers_to_test = [
    ("ollama", settings.OLLAMA_BASE_URL, None, settings.DEFAULT_LOCAL_MODEL),
    ("groq", settings.GROQ_BASE_URL or "https://api.groq.com/openai/v1", settings.GROQ_API_KEY, settings.DEFAULT_FAST_MODEL),
    ("openrouter", settings.OPENROUTER_BASE_URL or "https://openrouter.ai/api/v1", settings.OPENROUTER_API_KEY, settings.DEFAULT_REASONING_MODEL),
    ("nvidia", settings.NVIDIA_NIM_BASE_URL or "https://integrate.api.nvidia.com/v1", settings.NVIDIA_NIM_API_KEY, settings.DEFAULT_CODE_MODEL),
    ("mistral", settings.MISTRAL_BASE_URL or "https://api.mistral.ai/v1", settings.MISTRAL_API_KEY, "mistral-small-latest"),
    ("openai", "https://api.openai.com/v1", settings.OPENAI_API_KEY, settings.DEFAULT_MODEL),
    ("google", None, settings.GOOGLE_API_KEY or os.environ.get("GEMINI_API_KEY"), settings.DEFAULT_GEMINI_MODEL),
]

async def test_openai_compatible(name: str, base_url: str, api_key: Optional[str], model: str):
    print(f"\n--- Testing Provider: {name.upper()} ---")
    clean_key = (api_key or "").strip().strip('"').strip("'")
    print(f"Configured API Key Present: {bool(clean_key)} ({clean_key[:8]}...{clean_key[-4:] if len(clean_key) > 12 else ''})")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    
    if not clean_key and name != "ollama":
        print(f"FAILED: No API key loaded for {name}")
        return False, "No API Key"

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if clean_key:
        headers["Authorization"] = f"Bearer {clean_key}"
    if name == "openrouter":
        headers["HTTP-Referer"] = settings.OPENROUTER_HTTP_REFERER or "http://localhost"
        headers["X-Title"] = settings.OPENROUTER_X_TITLE or "AgentForge"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "What is AI? Answer in 1 short sentence."}],
        "stream": False,
        "max_tokens": 50,
        "temperature": 0.2
    }

    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            latency = (time.perf_counter() - start) * 1000
            print(f"HTTP Status: {resp.status_code}")
            print(f"Latency: {latency:.2f}ms")
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                print(f"SUCCESS! Response: {content.strip()}")
                return True, content
            else:
                print(f"FAILED! Response Body: {resp.text[:300]}")
                return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as exc:
        latency = (time.perf_counter() - start) * 1000
        print(f"FAILED with exception after {latency:.2f}ms: {exc}")
        return False, str(exc)

async def test_gemini(api_key: Optional[str], model: str):
    print(f"\n--- Testing Provider: GOOGLE (GEMINI) ---")
    clean_key = (api_key or "").strip().strip('"').strip("'")
    print(f"Configured API Key Present: {bool(clean_key)}")
    print(f"Model: {model}")

    if not clean_key:
        print("FAILED: No API key loaded for Google")
        return False, "No API Key"

    start = time.perf_counter()
    try:
        import google.generativeai as genai
        genai.configure(api_key=clean_key)
        gemini_model = genai.GenerativeModel(model)
        resp = gemini_model.generate_content("What is AI? Answer in 1 short sentence.")
        latency = (time.perf_counter() - start) * 1000
        print(f"Latency: {latency:.2f}ms")
        print(f"SUCCESS! Response: {resp.text.strip()}")
        return True, resp.text
    except Exception as exc:
        latency = (time.perf_counter() - start) * 1000
        print(f"FAILED after {latency:.2f}ms: {exc}")
        return False, str(exc)

async def main():
    results = {}
    for name, base_url, api_key, model in providers_to_test:
        if name == "google":
            success, msg = await test_gemini(api_key, model)
        else:
            success, msg = await test_openai_compatible(name, base_url, api_key, model)
        results[name] = (success, msg)

    print("\n" + "=" * 60)
    print("SUMMARY OF PROVIDERS:")
    print("=" * 60)
    for p, (ok, detail) in results.items():
        status_str = "WORKING" if ok else "FAILED"
        print(f"  {p.upper():<12}: {status_str} -> {detail[:80]}")

if __name__ == "__main__":
    asyncio.run(main())
