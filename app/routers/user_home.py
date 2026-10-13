from datetime import datetime

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.rewards import RewardsRepository
from app.services.rewards_service import RewardsService
from app.utilities.flash import flash
from . import router, templates


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    repo = RewardsRepository(db)
    service = RewardsService(repo)

    submissions = repo.get_student_submissions(user.id)
    approved_hours = service.calculate_approved_hours(submissions)
    milestones = repo.get_milestones()
    milestone_state = service.get_milestone_status(approved_hours, milestones)
    next_milestone = service.get_next_milestone_name(approved_hours, milestones)
    awards = repo.get_awards()
    redemptions = repo.get_user_redemptions(user.id)

    return templates.TemplateResponse(
        request=request,
        name="app.html",
        context={
            "user": user,
            "submissions": submissions,
            "latest_submission": submissions[0] if submissions else None,
            "approved_hours": approved_hours,
            "milestones": milestones,
            "milestone_state": milestone_state,
            "next_milestone": next_milestone,
            "awards": awards,
            "redemptions": redemptions,
            "student_id": user.id,
        },
    )


@router.post("/app/submit-hours")
async def submit_hours_action(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    organization: str = Form(...),
    hours: float = Form(...),
    description: str = Form(""),
):
    if hours <= 0:
        flash(request, "Volunteer hours must be greater than zero.", "danger")
        return RedirectResponse(url=request.url_for("user_home_view"), status_code=status.HTTP_303_SEE_OTHER)

    repo = RewardsRepository(db)
    repo.create_submission(
        student_id=user.id,
        organization=organization.strip(),
        hours=float(hours),
        description=description.strip(),
        status="pending",
        submission_date=datetime.utcnow(),
    )
    flash(request, "Your volunteer hours were submitted and are awaiting review.", "success")
    return RedirectResponse(url=request.url_for("user_home_view"), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/app/redeem-award/{award_id}")
async def redeem_award_action(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    award_id: int,
):
    repo = RewardsRepository(db)
    service = RewardsService(repo)
    award = repo.get_awards()
    selected = next((item for item in award if item.id == award_id), None)
    if selected is None:
        flash(request, "Award not found.", "danger")
        return RedirectResponse(url=request.url_for("user_home_view"), status_code=status.HTTP_303_SEE_OTHER)

    approved_hours = service.calculate_approved_hours(repo.get_student_submissions(user.id))
    if approved_hours < selected.required_hours:
        flash(request, f"You need {selected.required_hours} approved hours to redeem {selected.name}.", "danger")
        return RedirectResponse(url=request.url_for("user_home_view"), status_code=status.HTTP_303_SEE_OTHER)

    repo.create_redemption(student_id=user.id, award_id=award_id, status="pending")
    flash(request, f"Your {selected.name} redemption request was submitted.", "success")
    return RedirectResponse(url=request.url_for("user_home_view"), status_code=status.HTTP_303_SEE_OTHER)
