"""
Data export API routes — CSV/Excel export of crossing events.
"""

import csv
import io
from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.database import get_db
from app.models.crossing_event import CrossingEvent, Direction, MatchType
from app.models.user import User

router = APIRouter(prefix="/api/v2/export", tags=["Export"])


@router.get("/events")
async def export_events(
    format: str = Query(default="csv", regex="^(csv)$"),
    camera_id: Optional[uuid.UUID] = None,
    direction: Optional[Direction] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Export crossing events as CSV."""
    query = (
        select(CrossingEvent)
        .options(selectinload(CrossingEvent.bag_observations))
        .order_by(CrossingEvent.timestamp.desc())
    )

    if camera_id:
        query = query.where(CrossingEvent.camera_id == camera_id)
    if direction:
        query = query.where(CrossingEvent.direction == direction)
    if date_from:
        query = query.where(CrossingEvent.timestamp >= date_from)
    if date_to:
        query = query.where(CrossingEvent.timestamp <= date_to)

    result = await db.execute(query)
    events = result.scalars().all()

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Event ID", "Timestamp", "Camera ID", "Person ID",
        "Direction", "Match Type", "Fusion Score", "Coverage Score",
        "Needs Review", "Reviewed By", "Bags"
    ])

    for event in events:
        bags = ", ".join(
            f"{b.bag_type.value}({b.count})" for b in event.bag_observations
        )
        writer.writerow([
            str(event.id),
            event.timestamp.isoformat(),
            str(event.camera_id),
            str(event.person_id) if event.person_id else "",
            event.direction.value,
            event.match_type.value,
            f"{event.fusion_score:.3f}" if event.fusion_score else "",
            f"{event.coverage_score:.3f}" if event.coverage_score else "",
            event.needs_review,
            event.reviewed_by or "",
            bags,
        ])

    output.seek(0)
    filename = f"bordervision_events_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
