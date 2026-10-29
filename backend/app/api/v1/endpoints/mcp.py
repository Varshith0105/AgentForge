from fastapi import APIRouter, Depends
from app.api import deps
from app.models.user import User

router = APIRouter()


@router.get("/servers")
def list_mcp_servers(current_user: User = Depends(deps.get_current_user)):
    return {
        "servers": [
            {"name": "filesystem", "status": "available", "description": "File system operations"},
            {"name": "git", "status": "available", "description": "Git repository operations"},
            {"name": "github", "status": "available", "description": "GitHub API integration"},
            {"name": "browser", "status": "available", "description": "Browser automation"},
            {"name": "docker", "status": "available", "description": "Docker container management"},
        ]
    }


@router.post("/execute")
def execute_mcp_tool(payload: dict, current_user: User = Depends(deps.get_current_user)):
    return {
        "status": "executed",
        "tool": payload.get("tool"),
        "result": {},
    }
