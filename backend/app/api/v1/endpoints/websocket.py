from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.core.config import settings
from app.core.security import ALGORITHM
from app.core.database import get_db
from app.core.websocket_manager import ws_manager
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{channel}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel: str,
    token: str = Query(None),
    db: Session = Depends(get_db),
):
    """WebSocket endpoint for real-time communication."""
    # Authenticate
    user_email = None
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            token_type = payload.get("type")
            if token_type == "access":
                user_email = payload.get("sub")
        except JWTError:
            logger.warning(f"WS auth failed for channel {channel} — JWT error")

    if not user_email:
        # 4003 = custom auth failure (client watches for this to stop retrying)
        await websocket.close(code=4003, reason="Authentication failed")
        return

    await ws_manager.connect(websocket, channel, user_email)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "message")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "broadcast":
                await ws_manager.broadcast(channel, {
                    "type": "message",
                    "from": user_email,
                    "data": data.get("data"),
                })
            else:
                # Echo back with acknowledgment
                await websocket.send_json({
                    "type": "ack",
                    "received": data,
                })

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, channel)
        logger.info(f"WS disconnected: {user_email} from {channel}")
    except Exception as e:
        logger.error(f"WS error: {e}")
        await ws_manager.disconnect(websocket, channel)
