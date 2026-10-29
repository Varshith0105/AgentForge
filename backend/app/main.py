import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    init_db()

    # Initialize WebSocket background loops
    import asyncio
    from app.core.websocket_manager import ws_manager
    try:
        ws_manager.start_background_tasks(asyncio.get_running_loop())
        print("[OK] WebSocket Connection Manager started")
    except Exception as e:
        print(f"[WARN] WebSocket manager: {e}")

    # Initialize AI OS
    try:
        from app.core.ai import get_ai_orchestrator, get_provider_manager
        orchestrator = get_ai_orchestrator()
        provider_manager = get_provider_manager()
        print("[OK] AI Operating System initialized")
        print(f"     Models: {len(orchestrator.model_registry.list_models())}")
        print(f"     Templates: {len(orchestrator.prompt_manager.list_templates())}")
    except Exception as e:
        print(f"[WARN] AI OS: {e}")

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AgentForge - AI Software Engineering Platform",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
    }


import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Root project paths
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
dist_dir = os.path.join(project_root, "frontend", "dist")
dist_assets = os.path.join(dist_dir, "assets")

if os.path.exists(dist_assets):
    app.mount("/assets", StaticFiles(directory=dist_assets), name="assets")

@app.get("/app")
@app.get("/login")
@app.get("/register")
@app.get("/workspace")
@app.get("/workspace.html")
@app.get("/frontend/workspace.html")
def serve_spa():
    dist_index = os.path.join(dist_dir, "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index)
    return {"message": "AgentForge API operational"}

@app.get("/")
def root():
    dist_index = os.path.join(dist_dir, "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index)
    return {
        "message": "AgentForge API",
        "docs": "/docs",
        "health": "/health",
        "api": settings.API_V1_STR,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
