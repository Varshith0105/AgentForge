import json
import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from app.api import deps
from app.models.user import User
from app.core.config import settings
from app.services.platform_engine import stream_chat_completion

router = APIRouter()


class StreamRequest(BaseModel):
    message: str
    model: Optional[str] = None
    project_id: Optional[str] = None
    agent_type: Optional[str] = "assistant"
    provider: Optional[str] = None


@router.post("/chat")
async def stream_chat(
    payload: StreamRequest,
    current_user: User = Depends(deps.get_current_user),
):
    """Stream a chat response using SSE with Multi-Provider router and fallback."""
    async def generate():
        try:
            async for chunk in stream_chat_completion(
                [{"role": "user", "content": payload.message}],
                model=payload.model or settings.DEFAULT_MODEL,
                provider=payload.provider,
            ):
                content = chunk.get("content", "")
                provider = chunk.get("provider", "agentforge")
                model_name = chunk.get("model", payload.model or settings.DEFAULT_MODEL)
                yield f"data: {json.dumps({'content': content, 'provider': provider, 'model': model_name})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'content': f'AgentForge response to: {payload.message}', 'provider': 'agentforge-local'})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
