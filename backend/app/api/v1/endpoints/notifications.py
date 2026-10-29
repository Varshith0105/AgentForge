from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.core.database import get_db
from app.api import deps
from app.models.user import User

router = APIRouter()


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime


class NotificationReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    read_count: int


@router.get("")
def list_notifications(
    current_user: User = Depends(deps.get_current_user),
):
    """Return empty notifications list (can be extended with a Notification model)."""
    return {"notifications": [], "unread_count": 0}


@router.post("/read-all")
def mark_all_read(
    current_user: User = Depends(deps.get_current_user),
):
    return {"message": "All notifications marked as read", "read_count": 0}
