from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from app.api import deps
from app.core.config import settings
from app.models.user import User

router = APIRouter()


@router.get("/available")
def list_tools(current_user: User = Depends(deps.get_current_user)):
    return {
        "tools": [
            {"name": "read_file", "description": "Read a file from disk"},
            {"name": "write_file", "description": "Write content to a file"},
            {"name": "list_directory", "description": "List files in a directory"},
            {"name": "search_code", "description": "Search for code patterns"},
            {"name": "git_status", "description": "Get git repository status"},
            {"name": "git_commit", "description": "Commit changes to git"},
            {"name": "github_search", "description": "Search GitHub repositories"},
        ]
    }


@router.post("/execute")
def execute_tool(payload: dict, current_user: User = Depends(deps.get_current_user)):
    tool_name = payload.get("tool")
    args = payload.get("args", {})

    root = Path(settings.WORKSPACE_ROOT).resolve()

    def safe_path(value: str, directory: bool = False) -> Path:
        candidate = (root / value).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise HTTPException(status_code=403, detail="Path is outside the workspace") from exc
        if directory and not candidate.is_dir():
            raise HTTPException(status_code=404, detail="Directory not found")
        return candidate

    if tool_name == "read_file":
        path = safe_path(args.get("path", ""))
        if path.is_file():
            return {"result": path.read_text(encoding="utf-8", errors="ignore"), "success": True}
        return {"result": None, "success": False, "error": "File not found"}

    elif tool_name == "list_directory":
        path = safe_path(args.get("path", "."), directory=True)
        items = [{"name": item.name, "type": "dir" if item.is_dir() else "file"} for item in path.iterdir()]
        return {"result": items, "success": True}

    elif tool_name == "run_command":
        raise HTTPException(status_code=503, detail="Command execution is disabled")

    return {"result": None, "success": False, "error": f"Unknown tool: {tool_name}"}
