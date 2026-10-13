from datetime import datetime

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AdminDep
from app.dependencies.session import SessionDep
from app.repositories.rewards import RewardsRepository
from app.repositories.user import UserRepository
from app.services.rewards_service import RewardsService
from app.utilities.flash import flash
from . import router, templates


@router.get("/admin", response_class=HTMLResponse)
async def admin_home_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    repo = RewardsRepository(db)
    user_repo = UserRepository(db)
    service = RewardsService(repo)
    pending = repo.get_pending_submissions()
    submissions_by_user = {}
    for submission in pending:
        student = user_repo.get_by_id(submission.student_id)
        submissions_by_user[submission.id] = student

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "user": user,
            "pending_submissions": pending,
            "student_lookup": submissions_by_user,
            "service": service,
            "approved_hours_by_student": {
                sub.id: service.calculate_approved_hours(repo.get_student_submissions(sub.student_id))
                for sub in pending
            },
        },
    )


@router.post("/admin/review/{submission_id}")
async def review_submission_action(
    request: Request,
    user: AdminDep,
    db: SessionDep,
    submission_id: int,
    decision: str = Form(...),
    review_notes: str = Form(""),
):
    repo = RewardsRepository(db)
    service = RewardsService(repo)
    submission = repo.get_submission_by_id(submission_id)
    if submission is None:
        flash(request, "Submission was not found.", "danger")
        return RedirectResponse(url=request.url_for("admin_home_view"), status_code=status.HTTP_303_SEE_OTHER)

    final_status = decision.lower() == "approve" and "approved" or "rejected"
    repo.update_submission(
        submission,
        status=final_status,
        reviewed_by=user.id,
        reviewed_at=datetime.utcnow(),
        review_notes=review_notes.strip() or None,
    )

    if final_status == "approved":
        service.sync_student_milestones(submission.student_id, service.calculate_approved_hours(repo.get_student_submissions(submission.student_id)))
        flash(request, "Submission approved and milestone progress updated.", "success")
    else:
        flash(request, "Submission rejected. The student may resubmit new hours.", "warning")

    return RedirectResponse(url=request.url_for("admin_home_view"), status_code=status.HTTP_303_SEE_OTHER)
