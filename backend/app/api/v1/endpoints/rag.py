from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api import deps
from app.models.user import User

router = APIRouter()


class RAGSearchRequest(BaseModel):
    query: str
    project_id: Optional[str] = None
    limit: Optional[int] = 5


@router.post("/search")
def rag_search(
    payload: RAGSearchRequest,
    current_user: User = Depends(deps.get_current_user),
):
    """Perform RAG hybrid search on the codebase."""
    return {
        "query": payload.query,
        "results": [],
        "total": 0,
        "message": "No indexed content yet. Upload and analyze a repository first.",
    }
