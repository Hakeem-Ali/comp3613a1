from sqlmodel import Session, SQLModel, create_engine

from app.models.rewards import Award, Milestone, StudentMilestone, VolunteerSubmission
from app.services.rewards_service import RewardsService


class DummyRepo:
    def __init__(self):
        self.submissions = []
        self.awards = []
        self.milestones = []
        self.student_milestones = []

    def get_pending_submissions(self):
        return []

    def get_student_submissions(self, _user_id):
        return []

    def get_user_milestones(self, _user_id):
        return []

    def get_awards(self):
        return []

    def get_user_redemptions(self, _user_id):
        return []

    def create_submission(self, **kwargs):
        return VolunteerSubmission(**kwargs)

    def create_redemption(self, **kwargs):
        return kwargs


def test_milestone_thresholds_and_award_eligibility():
    service = RewardsService(DummyRepo())

    assert service.calculate_approved_hours([]) == 0
    assert service.is_award_eligible(0, 4, []) is False
    assert service.is_award_eligible(10, 4, []) is True
    assert service.get_next_milestone_name(0, []) == "Community Starter"


def test_build_milestone_state_tracks_current_and_next():
    service = RewardsService(DummyRepo())
    milestones = [
        Milestone(id=1, name="Bronze Contributor", required_hours=10),
        Milestone(id=2, name="Silver Contributor", required_hours=40),
    ]

    state = service.build_milestone_state(20, milestones)

    assert state["current"] == "Bronze Contributor"
    assert state["next"] == "Silver Contributor"
    assert state["progress"] == 50.0
