from fastapi import APIRouter, Depends
from app.api import deps
from app.models.user import User

router = APIRouter()


@router.get("/available")
def list_tools(current_user: User = Depends(deps.get_current_user)):
    return {
        "tools": [
            {"name": "read_file", "description": "Read a file from disk"},
            {"name": "write_file", "description": "Write content to a file"},
            {"name": "list_directory", "description": "List files in a directory"},
            {"name": "run_command", "description": "Run a shell command"},
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

    if tool_name == "read_file":
        import os
        path = args.get("path", "")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return {"result": f.read(), "success": True}
        return {"result": None, "success": False, "error": "File not found"}

    elif tool_name == "list_directory":
        import os
        path = args.get("path", ".")
        if os.path.exists(path):
            items = []
            for item in os.listdir(path):
                full = os.path.join(path, item)
                items.append({"name": item, "type": "dir" if os.path.isdir(full) else "file"})
            return {"result": items, "success": True}
        return {"result": [], "success": False, "error": "Directory not found"}

    elif tool_name == "run_command":
        import subprocess
        cmd = args.get("command", "")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return {
            "result": {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode},
            "success": result.returncode == 0,
        }

    return {"result": None, "success": False, "error": f"Unknown tool: {tool_name}"}
