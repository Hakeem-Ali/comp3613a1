from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Milestone(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    required_hours: int = Field(default=0, ge=0)
    description: str = ""
    badge_icon: str = "medal"
    display_order: int = Field(default=0)


class StudentMilestone(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="user.id", index=True)
    milestone_id: int = Field(foreign_key="milestone.id", index=True)
    earned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VolunteerSubmission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="user.id", index=True)
    organization: str
    hours: float = Field(ge=0)
    description: str = ""
    submission_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = Field(default="pending")
    reviewed_by: Optional[int] = Field(default=None, foreign_key="user.id")
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None


class Award(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    required_hours: int = Field(default=0, ge=0)
    description: str = ""
    icon: str = "gift"
    active: bool = Field(default=True)


class AwardRedemption(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="user.id", index=True)
    award_id: int = Field(foreign_key="award.id", index=True)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = Field(default="pending")
    notes: Optional[str] = None
