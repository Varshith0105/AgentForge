from fastapi import APIRouter
from app.api.v1.endpoints import (
    agents, analysis, auth, chats, github, projects, rag, ai_os,
    websocket, streaming, jobs, notifications, observability, knowledge_engine, tools, terminal, git, mcp, costs, files
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(github.router, prefix="/github", tags=["github"])
api_router.include_router(git.router, prefix="/git", tags=["git"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(knowledge_engine.router, prefix="/knowledge-engine", tags=["knowledge-engine"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(chats.router, prefix="/chats", tags=["chats"])
api_router.include_router(ai_os.router, prefix="/ai-os", tags=["ai-operating-system"])
api_router.include_router(tools.router, prefix="/tools", tags=["tool-execution-engine"])
api_router.include_router(mcp.router, prefix="/mcp", tags=["model-context-protocol"])
api_router.include_router(terminal.router, prefix="/terminal", tags=["terminal"])
api_router.include_router(costs.router, prefix="/costs", tags=["cost-tracking"])
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(streaming.router, prefix="/streaming", tags=["streaming"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(observability.router, prefix="/observability", tags=["observability"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
