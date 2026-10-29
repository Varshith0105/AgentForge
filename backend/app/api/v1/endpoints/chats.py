import uuid
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from app.core.database import get_db
from app.api import deps
from app.models.user import User
from app.models.models import Chat, Message, Project
from app.services.platform_engine import estimate_cost, estimate_tokens, repository_memory, stream_chat_completion

router = APIRouter()


class ChatCreate(BaseModel):
    project_id: Optional[str] = None
    title: Optional[str] = "New Chat"
    model: Optional[str] = None       # None = use auto-routing
    provider: Optional[str] = None    # None = use auto-routing


class MessageCreate(BaseModel):
    content: str
    stream: Optional[bool] = False
    model: Optional[str] = None
    provider: Optional[str] = None
    task_type: Optional[str] = None  # 'coding','reasoning','chat','quick','fast'


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    project_id: Optional[str]
    model: Optional[str]
    total_tokens: int
    total_cost: float
    created_at: datetime


@router.get("", response_model=List[ChatResponse])
def list_chats(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    chats = db.query(Chat).filter(Chat.user_id == current_user.id).order_by(Chat.created_at.desc()).all()
    return chats


@router.post("", response_model=ChatResponse, status_code=201)
def create_chat(
    payload: ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    chat = Chat(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        project_id=payload.project_id,
        title=payload.title or "New Chat",
        model=payload.model,
        provider=payload.provider,
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/{chat_id}/messages", response_model=List[MessageResponse])
def get_chat_messages(
    chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat.messages


@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    from fastapi.responses import StreamingResponse

    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    project_context = ""
    if chat.project_id:
        project = db.query(Project).filter(Project.id == chat.project_id, Project.owner_id == current_user.id).first()
        project_repo_path = str(getattr(project, "repo_path", "") or "") if project else ""
        if project_repo_path:
            memory = repository_memory(project_repo_path)
            project_context = memory.get("context_summary", "")

    # Save user message
    user_msg = Message(
        id=str(uuid.uuid4()),
        chat_id=chat_id,
        role="user",
        content=payload.content,
    )
    db.add(user_msg)
    db.commit()

    # Get conversation history
    history = []
    if project_context:
        history.append({"role": "system", "content": f"Use the repository context below when answering.\n{project_context}"})
    history.extend({"role": m.role, "content": m.content} for m in chat.messages)

    async def stream_response():
        accumulated = ""
        prompt_tokens = 0
        try:
            prompt_tokens = sum(estimate_tokens(message["content"]) for message in history)
            async for chunk in stream_chat_completion(
                history,
                model=payload.model or chat.model,
                provider=payload.provider or chat.provider,
                task_type=payload.task_type,
            ):
                content = chunk.get("content", "")
                is_done_meta = chunk.get("done", False)
                if content:
                    accumulated += content
                    yield f"data: {json.dumps({'content': content, 'model': chunk.get('model'), 'provider': chunk.get('provider'), 'is_local': chunk.get('is_local', False)})}\n\n"
                elif is_done_meta:
                    # Metadata sentinel — latency + token count, no text content
                    yield f"data: {json.dumps({'meta': True, 'model': chunk.get('model'), 'provider': chunk.get('provider'), 'is_local': chunk.get('is_local', False), 'latency_ms': chunk.get('latency_ms', 0), 'tokens': chunk.get('tokens', 0)})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            # Save assistant message
            if accumulated:
                completion_tokens = estimate_tokens(accumulated)
                asst_msg = Message(
                    id=str(uuid.uuid4()),
                    chat_id=chat_id,
                    role="assistant",
                    content=accumulated,
                    model=payload.model or chat.model,
                    tokens_used=completion_tokens,
                    cost=estimate_cost(payload.provider or chat.provider or "openrouter", payload.model or chat.model, prompt_tokens, completion_tokens),
                )
                db.add(asst_msg)
                chat.total_tokens += completion_tokens
                chat.total_cost += asst_msg.cost or 0.0
                db.commit()
            yield "data: [DONE]\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")


@router.delete("/{chat_id}")
def delete_chat(
    chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    db.delete(chat)
    db.commit()
    return {"message": "Chat deleted"}
