from datetime import datetime
from fastapi import APIRouter, Depends
from app.api import deps
from app.models.user import User

router = APIRouter()


@router.get("/summary")
def get_cost_summary(current_user: User = Depends(deps.get_current_user)):
    return {
        "total_cost": 0.0,
        "total_tokens": 0,
        "by_provider": {},
        "by_model": {},
        "period": "all_time",
        "currency": "USD",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/breakdown")
def get_cost_breakdown(current_user: User = Depends(deps.get_current_user)):
    return {
        "daily": [],
        "by_model": [],
        "by_project": [],
    }
