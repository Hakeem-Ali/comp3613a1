"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.rewards import Award, AwardRedemption, Milestone, StudentMilestone, VolunteerSubmission
from app.models.user import User

__all__ = [
    "User",
    "Milestone",
    "StudentMilestone",
    "VolunteerSubmission",
    "Award",
    "AwardRedemption",
]
