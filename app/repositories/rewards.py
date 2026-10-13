from typing import Optional

from sqlmodel import Session, select

from app.models.rewards import Award, AwardRedemption, Milestone, StudentMilestone, VolunteerSubmission


class RewardsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_milestones(self) -> list[Milestone]:
        return self.db.exec(select(Milestone).order_by(Milestone.required_hours)).all()

    def get_pending_submissions(self) -> list[VolunteerSubmission]:
        return self.db.exec(
            select(VolunteerSubmission).where(VolunteerSubmission.status == "pending").order_by(VolunteerSubmission.submission_date.desc())
        ).all()

    def get_student_submissions(self, student_id: int) -> list[VolunteerSubmission]:
        return self.db.exec(
            select(VolunteerSubmission).where(VolunteerSubmission.student_id == student_id).order_by(VolunteerSubmission.submission_date.desc())
        ).all()

    def get_user_milestones(self, student_id: int) -> list[StudentMilestone]:
        return self.db.exec(
            select(StudentMilestone).where(StudentMilestone.student_id == student_id).order_by(StudentMilestone.earned_at.desc())
        ).all()

    def get_awards(self) -> list[Award]:
        return self.db.exec(select(Award).where(Award.active == True).order_by(Award.required_hours)).all()

    def get_user_redemptions(self, student_id: int) -> list[AwardRedemption]:
        return self.db.exec(
            select(AwardRedemption).where(AwardRedemption.student_id == student_id).order_by(AwardRedemption.requested_at.desc())
        ).all()

    def get_submission_by_id(self, submission_id: int) -> Optional[VolunteerSubmission]:
        return self.db.get(VolunteerSubmission, submission_id)

    def create_submission(self, **data) -> VolunteerSubmission:
        submission = VolunteerSubmission(**data)
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)
        return submission

    def update_submission(self, submission: VolunteerSubmission, **updates) -> VolunteerSubmission:
        for key, value in updates.items():
            setattr(submission, key, value)
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)
        return submission

    def create_redemption(self, **data) -> AwardRedemption:
        redemption = AwardRedemption(**data)
        self.db.add(redemption)
        self.db.commit()
        self.db.refresh(redemption)
        return redemption

    def get_student_milestone(self, student_id: int, milestone_id: int) -> Optional[StudentMilestone]:
        return self.db.exec(
            select(StudentMilestone).where(
                (StudentMilestone.student_id == student_id) & (StudentMilestone.milestone_id == milestone_id)
            )
        ).one_or_none()

    def award_milestone(self, student_id: int, milestone_id: int) -> StudentMilestone:
        existing = self.get_student_milestone(student_id, milestone_id)
        if existing is not None:
            return existing
        entry = StudentMilestone(student_id=student_id, milestone_id=milestone_id)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
