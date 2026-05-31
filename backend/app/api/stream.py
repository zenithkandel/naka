"""
Video streaming and WebSocket API routes.
"""

import asyncio

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.core.security import get_current_user
from app.core.websocket_manager import event_manager, video_manager
from app.models.user import User

router = APIRouter(tags=["Streaming"])


# Shared buffer for the latest annotated frame (set by vision pipeline)
_latest_frame: bytes = b""
_frame_event = asyncio.Event()


def update_frame(frame_bytes: bytes):
    """Called by the vision pipeline to push new annotated frames."""
    global _latest_frame
    _latest_frame = frame_bytes
    _frame_event.set()


async def _mjpeg_generator():
    """Generate MJPEG stream from the latest annotated frame."""
    while True:
        await _frame_event.wait()
        _frame_event.clear()
        if _latest_frame:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + _latest_frame
                + b"\r\n"
            )


@router.get("/api/v2/stream/live")
async def live_stream(_: User = Depends(get_current_user)):
    """
    Live MJPEG video stream with bounding box overlays.
    Connect via <img src="/api/v2/stream/live"> in the frontend.
    """
    return StreamingResponse(
        _mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """
    WebSocket endpoint for real-time crossing event notifications.
    Pushes JSON event data as crossings are detected.
    """
    await event_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; client can send pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        event_manager.disconnect(websocket)


@router.websocket("/ws/video")
async def websocket_video(websocket: WebSocket):
    """
    WebSocket endpoint for video frame streaming (binary).
    Alternative to MJPEG for clients that need WebSocket transport.
    """
    await video_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        video_manager.disconnect(websocket)
