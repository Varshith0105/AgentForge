import subprocess
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api import deps
from app.models.user import User

router = APIRouter()


class TerminalRequest(BaseModel):
    command: str
    cwd: Optional[str] = None


BLOCKED_COMMANDS = ["rm -rf /", "format", "del /f /s /q c:\\", "shutdown", "reboot"]


@router.post("/execute")
def execute_command(
    payload: TerminalRequest,
    current_user: User = Depends(deps.get_current_user),
):
    """Execute a terminal command safely."""
    cmd = payload.command.strip()

    # Security: block dangerous commands
    for blocked in BLOCKED_COMMANDS:
        if blocked.lower() in cmd.lower():
            raise HTTPException(status_code=403, detail=f"Command blocked for security: {cmd}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=payload.cwd or os.getcwd(),
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "command": cmd,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timed out after 30 seconds")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
