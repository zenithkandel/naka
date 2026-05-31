"""
Pydantic schemas for request/response validation.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.crossing_event import Direction, MatchType
from app.models.bag_observation import BagType
from app.models.user import UserRole


# ─── Auth ──────────────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: str
    password: str = Field(min_length=6)
    role: UserRole = UserRole.VIEWER

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Camera ────────────────────────────────────────────────────
class CameraCreate(BaseModel):
    name: str
    source_url: str
    description: Optional[str] = None

class CameraCalibration(BaseModel):
    intrinsic_matrix: Optional[list] = None
    homography_matrix: Optional[list] = None
    camera_height_m: Optional[float] = None
    tilt_deg: Optional[float] = None
    focal_length_px: Optional[float] = None
    principal_point: Optional[list] = None

class CameraBoundary(BaseModel):
    start: List[float] = Field(description="[x, y] start point")
    end: List[float] = Field(description="[x, y] end point")

class CameraResponse(BaseModel):
    id: uuid.UUID
    name: str
    source_url: str
    description: Optional[str]
    intrinsic_matrix: Optional[dict]
    homography_matrix: Optional[dict]
    boundary_line: Optional[dict]
    camera_height_m: Optional[float]
    tilt_deg: Optional[float]
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Crossing Event ───────────────────────────────────────────
class BagObservationResponse(BaseModel):
    bag_type: BagType
    count: int
    confidence: float
    model_config = {"from_attributes": True}

class CrossingEventResponse(BaseModel):
    id: uuid.UUID
    camera_id: uuid.UUID
    person_id: Optional[uuid.UUID]
    timestamp: datetime
    direction: Direction
    match_type: MatchType
    fusion_score: Optional[float]
    coverage_score: Optional[float]
    needs_review: bool
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    bag_observations: List[BagObservationResponse] = []
    model_config = {"from_attributes": True}

class EventReview(BaseModel):
    approved: bool
    notes: Optional[str] = None

class EventFilter(BaseModel):
    camera_id: Optional[uuid.UUID] = None
    person_id: Optional[uuid.UUID] = None
    direction: Optional[Direction] = None
    match_type: Optional[MatchType] = None
    needs_review: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# ─── Person ────────────────────────────────────────────────────
class PersonResponse(BaseModel):
    id: uuid.UUID
    display_name: Optional[str]
    first_seen: datetime
    last_seen: datetime
    height_cm: Optional[float]
    height_confidence: Optional[float]
    body_ratios: Optional[dict]
    total_crossings: int
    total_entries: int
    total_exits: int
    created_at: datetime
    model_config = {"from_attributes": True}

class PersonDetail(PersonResponse):
    crossing_events: List[CrossingEventResponse] = []
    notes: Optional[str]


# ─── Analytics ─────────────────────────────────────────────────
class DailyAnalytics(BaseModel):
    date: str
    entries: int
    exits: int
    unique_persons: int
    bags_detected: int

class DashboardStats(BaseModel):
    current_occupancy: int
    today_entries: int
    today_exits: int
    today_bags: int
    pending_reviews: int
    active_cameras: int
