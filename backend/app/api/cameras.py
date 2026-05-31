"""
Camera management API routes.
"""

from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.database import get_db
from app.models.camera import Camera
from app.models.user import User, UserRole
from app.schemas.schemas import (
    CameraBoundary,
    CameraCalibration,
    CameraCreate,
    CameraResponse,
)

router = APIRouter(prefix="/api/v2/cameras", tags=["Cameras"])


@router.get("/", response_model=List[CameraResponse])
async def list_cameras(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all cameras."""
    result = await db.execute(select(Camera).order_by(Camera.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    data: CameraCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    """Create a new camera configuration (admin only)."""
    camera = Camera(name=data.name, source_url=data.source_url, description=data.description)
    db.add(camera)
    await db.flush()
    await db.refresh(camera)
    return camera


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get camera details."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera


@router.put("/{camera_id}/calibrate", response_model=CameraResponse)
async def calibrate_camera(
    camera_id: uuid.UUID,
    calibration: CameraCalibration,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN, UserRole.OPERATOR)),
):
    """Update camera calibration parameters."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    for field, value in calibration.model_dump(exclude_unset=True).items():
        setattr(camera, field, value)

    await db.flush()
    await db.refresh(camera)
    return camera


@router.put("/{camera_id}/boundary", response_model=CameraResponse)
async def set_boundary(
    camera_id: uuid.UUID,
    boundary: CameraBoundary,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN, UserRole.OPERATOR)),
):
    """Set the virtual boundary line for a camera."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    camera.boundary_line = {"start": boundary.start, "end": boundary.end}
    await db.flush()
    await db.refresh(camera)
    return camera
