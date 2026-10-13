from __future__ import annotations

from typing import Iterable

from app.models.rewards import Award, Milestone, StudentMilestone, VolunteerSubmission


class RewardsService:
    DEFAULT_MILESTONES = [
        {"name": "Bronze Contributor", "required_hours": 10, "description": "First volunteer milestone", "badge_icon": "milestone", "display_order": 1},
        {"name": "Silver Contributor", "required_hours": 40, "description": "Steady campus impact", "badge_icon": "milestone", "display_order": 2},
        {"name": "Gold Contributor", "required_hours": 80, "description": "Major campus contribution", "badge_icon": "trophy", "display_order": 3},
        {"name": "Platinum Contributor", "required_hours": 120, "description": "Top campus volunteer", "badge_icon": "workspace_premium", "display_order": 4},
    ]

    def __init__(self, repo):
        self.repo = repo

    def calculate_approved_hours(self, submissions: Iterable[VolunteerSubmission]) -> float:
        return sum(float(item.hours) for item in submissions if getattr(item, "status", "") == "approved")

    def get_next_milestone_name(self, approved_hours: float, milestones: list[Milestone] | None = None) -> str:
        milestone_list = sorted((milestones or []), key=lambda item: item.required_hours)
        if not milestone_list:
            return "Community Starter"
        for milestone in milestone_list:
            if approved_hours < milestone.required_hours:
                return milestone.name
        return "All milestones unlocked"

    def is_award_eligible(self, approved_hours: float, required_hours: float, _redemptions: list | None = None) -> bool:
        return approved_hours >= required_hours

    def get_milestone_status(self, approved_hours: float, milestones: list[Milestone] | None = None):
        ordered = sorted((milestones or []), key=lambda item: item.required_hours)
        progress = []
        for milestone in ordered:
            progress.append({
                "name": milestone.name,
                "required_hours": milestone.required_hours,
                "earned": approved_hours >= milestone.required_hours,
                "in_progress": approved_hours >= milestone.required_hours - 10 and approved_hours < milestone.required_hours,
                "current": approved_hours,
            })
        return progress

    def build_milestone_state(self, approved_hours: float, milestones: list[Milestone] | None = None):
        ordered = sorted((milestones or []), key=lambda item: item.required_hours)
        if not ordered:
            return {"current": "Community Starter", "next": "Community Starter", "progress": 0, "approved_hours": approved_hours}

        earned = [item for item in ordered if approved_hours >= item.required_hours]
        current_name = earned[-1].name if earned else "Community Starter"
        next_milestone = next((item for item in ordered if approved_hours < item.required_hours), None)

        if next_milestone is None:
            next_name = "All milestones unlocked"
            progress = 100.0
        elif next_milestone.required_hours > 0:
            progress = min(100.0, max(0.0, (approved_hours / next_milestone.required_hours) * 100))
            next_name = next_milestone.name
        else:
            progress = 0.0
            next_name = next_milestone.name

        return {
            "current": current_name,
            "next": next_name,
            "progress": round(progress, 1),
            "approved_hours": approved_hours,
        }

    def sync_student_milestones(self, student_id: int, approved_hours: float):
        milestones = self.repo.get_milestones()
        for milestone in sorted(milestones, key=lambda item: item.required_hours):
            if approved_hours >= milestone.required_hours:
                self.repo.award_milestone(student_id, milestone.id)
        return self.repo.get_user_milestones(student_id)
