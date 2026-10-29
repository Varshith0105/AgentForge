import os
import shlex
import subprocess
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api import deps
from app.models.user import User
from app.core.config import settings

router = APIRouter()


class TerminalRequest(BaseModel):
    command: str
    cwd: Optional[str] = None


ALLOWED_COMMANDS = {"git", "node", "npm", "python", "pytest", "echo", "dir", "type"}


def _workspace_path(path: Optional[str]) -> Path:
    root = Path(settings.WORKSPACE_ROOT).resolve()
    candidate = (root / (path or ".")).resolve() if not os.path.isabs(path or "") else Path(path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Working directory is outside the workspace") from exc
    if not candidate.is_dir():
        raise HTTPException(status_code=400, detail="Working directory does not exist")
    return candidate


@router.post("/execute")
def execute_command(
    payload: TerminalRequest,
    current_user: User = Depends(deps.get_current_user),
):
    """Execute an allowlisted command inside the configured workspace."""
    if not settings.ENABLE_TERMINAL:
        raise HTTPException(status_code=503, detail="Terminal execution is disabled")
    cmd = payload.command.strip()
    try:
        argv = shlex.split(cmd, posix=False)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid command syntax") from exc
    if not argv or argv[0].lower() not in ALLOWED_COMMANDS:
        raise HTTPException(status_code=403, detail="Command is not allowed")

    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=_workspace_path(payload.cwd),
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "command": cmd,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timed out after 30 seconds")
    except OSError as exc:
        raise HTTPException(status_code=400, detail=f"Command could not be started: {exc}") from exc
