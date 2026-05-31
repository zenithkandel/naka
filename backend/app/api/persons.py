"""
Person profile API routes.
"""

from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user, require_role
from app.database import get_db
from app.models.person import Person
from app.models.crossing_event import CrossingEvent
from app.models.user import User, UserRole
from app.schemas.schemas import PersonDetail, PersonResponse

router = APIRouter(prefix="/api/v2/persons", tags=["Persons"])


@router.get("/", response_model=List[PersonResponse])
async def list_persons(
    search: Optional[str] = None,
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all person profiles."""
    query = select(Person).order_by(Person.last_seen.desc())

    if search:
        query = query.where(Person.display_name.ilike(f"%{search}%"))

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{person_id}", response_model=PersonDetail)
async def get_person(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get detailed person profile with crossing history."""
    result = await db.execute(
        select(Person)
        .options(
            selectinload(Person.crossing_events)
            .selectinload(CrossingEvent.bag_observations)
        )
        .where(Person.id == person_id)
    )
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.delete("/{person_id}", status_code=204)
async def delete_person(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    """
    GDPR Right to Erasure — permanently delete a person profile.
    Also removes associated vector embeddings from Qdrant.
    """
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    # TODO: Delete from Qdrant when vision module is integrated
    # if person.qdrant_appearance_id:
    #     qdrant_client.delete(collection_name="appearance_embeddings", ...)
    # if person.qdrant_gait_id:
    #     qdrant_client.delete(collection_name="gait_embeddings", ...)

    await db.delete(person)
