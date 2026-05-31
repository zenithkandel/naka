"""
Crossing events API routes.
"""

from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user, require_role
from app.database import get_db
from app.models.crossing_event import CrossingEvent, Direction, MatchType
from app.models.user import User, UserRole
from app.schemas.schemas import CrossingEventResponse, DashboardStats, EventReview

router = APIRouter(prefix="/api/v2/events", tags=["Events"])


@router.get("/", response_model=List[CrossingEventResponse])
async def list_events(
    camera_id: Optional[uuid.UUID] = None,
    person_id: Optional[uuid.UUID] = None,
    direction: Optional[Direction] = None,
    match_type: Optional[MatchType] = None,
    needs_review: Optional[bool] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List crossing events with optional filters."""
    query = (
        select(CrossingEvent)
        .options(selectinload(CrossingEvent.bag_observations))
        .order_by(CrossingEvent.timestamp.desc())
    )

    if camera_id:
        query = query.where(CrossingEvent.camera_id == camera_id)
    if person_id:
        query = query.where(CrossingEvent.person_id == person_id)
    if direction:
        query = query.where(CrossingEvent.direction == direction)
    if match_type:
        query = query.where(CrossingEvent.match_type == match_type)
    if needs_review is not None:
        query = query.where(CrossingEvent.needs_review == needs_review)
    if date_from:
        query = query.where(CrossingEvent.timestamp >= date_from)
    if date_to:
        query = query.where(CrossingEvent.timestamp <= date_to)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/{event_id}/review", response_model=CrossingEventResponse)
async def review_event(
    event_id: uuid.UUID,
    review: EventReview,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.OPERATOR, UserRole.ADMIN)),
):
    """Mark an event as reviewed by an operator."""
    result = await db.execute(
        select(CrossingEvent)
        .options(selectinload(CrossingEvent.bag_observations))
        .where(CrossingEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event.needs_review = False
    event.reviewed_by = current_user.username
    event.reviewed_at = datetime.utcnow()
    await db.flush()
    await db.refresh(event)
    return event


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get real-time dashboard statistics."""
    from app.models.camera import Camera
    from app.models.bag_observation import BagObservation

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Today's entries
    entries = await db.execute(
        select(func.count(CrossingEvent.id)).where(
            CrossingEvent.timestamp >= today_start,
            CrossingEvent.direction == Direction.IN,
        )
    )
    today_entries = entries.scalar() or 0

    # Today's exits
    exits = await db.execute(
        select(func.count(CrossingEvent.id)).where(
            CrossingEvent.timestamp >= today_start,
            CrossingEvent.direction == Direction.OUT,
        )
    )
    today_exits = exits.scalar() or 0

    # Today's bags
    bags = await db.execute(
        select(func.coalesce(func.sum(BagObservation.count), 0)).join(
            CrossingEvent
        ).where(CrossingEvent.timestamp >= today_start)
    )
    today_bags = bags.scalar() or 0

    # Pending reviews
    pending = await db.execute(
        select(func.count(CrossingEvent.id)).where(CrossingEvent.needs_review == True)
    )
    pending_reviews = pending.scalar() or 0

    # Active cameras
    active_cams = await db.execute(
        select(func.count(Camera.id)).where(Camera.is_active == True)
    )

    return DashboardStats(
        current_occupancy=max(0, today_entries - today_exits),
        today_entries=today_entries,
        today_exits=today_exits,
        today_bags=today_bags,
        pending_reviews=pending_reviews,
        active_cameras=active_cams.scalar() or 0,
    )
