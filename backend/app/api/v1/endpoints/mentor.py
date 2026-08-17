from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.tenant import get_current_tenant, TenantContext
from app.core.permissions import require_role, Permission
from app.models.organization import OrgRole
from app.models.candidate import Candidate
from app.models.student_profile import StudentProfile
from app.models.resume import Resume
from app.models.application import Application, Interview
from app.models.candidate_interaction import CandidateInteraction
from app.models.activity import Followup, FollowupStatus
from app.services.resume_service import calculate_profile_completeness

router = APIRouter()

@router.get("/students", summary="Get Authorized Students for Mentor Dashboard")
def get_mentor_students(
    ctx: TenantContext = Depends(require_role(OrgRole.ADMIN, OrgRole.MENTOR, OrgRole.COUNSELOR, OrgRole.RECRUITER)),
    db: Session = Depends(get_db)
):
    role_str = ctx.role.value if hasattr(ctx.role, "value") else str(ctx.role).upper()

    # Mentors can view candidates where they are assigned as counselor/recruiter, or all org candidates if admin/counselor/recruiter
    query = db.query(Candidate).filter(Candidate.organization_id == ctx.organization.id)
    if role_str == "MENTOR":
        # Strictly filter assigned students for mentors
        query = query.filter(
            (Candidate.assigned_counselor_id == ctx.user.id) |
            (Candidate.assigned_recruiter_id == ctx.user.id) |
            (Candidate.user_id == ctx.user.id)
        )

    candidates = query.order_by(Candidate.id.desc()).all()
    results = []

    attention_flags_summary = {
        "missing_resume": 0,
        "incomplete_profile": 0,
        "overdue_followups": 0,
        "interviews_scheduled": 0
    }

    for cand in candidates:
        profile = db.query(StudentProfile).filter(StudentProfile.candidate_id == cand.id).first()
        resumes_count = db.query(Resume).filter(Resume.candidate_id == cand.id).count()
        apps_count = db.query(Application).filter(Application.candidate_id == cand.id).count()
        interactions_count = db.query(CandidateInteraction).filter(CandidateInteraction.candidate_id == cand.id).count()
        interviews_count = db.query(Interview).join(Application).filter(Application.candidate_id == cand.id).count()

        comp = calculate_profile_completeness(cand, profile)
        completeness = comp["completeness_score"]

        attention_reasons = []
        if resumes_count == 0:
            attention_reasons.append("Missing Resume")
            attention_flags_summary["missing_resume"] += 1
        if completeness < 80:
            attention_reasons.append(f"Incomplete Profile ({completeness}%)")
            attention_flags_summary["incomplete_profile"] += 1
        if interviews_count > 0:
            attention_flags_summary["interviews_scheduled"] += 1

        results.append({
            "id": cand.id,
            "full_name": cand.full_name,
            "email": cand.email,
            "phone": cand.phone,
            "location": cand.location,
            "status": cand.status.value if cand.status else "NEW",
            "completeness_score": completeness,
            "resumes_count": resumes_count,
            "applications_count": apps_count,
            "interactions_count": interactions_count,
            "interviews_count": interviews_count,
            "attention_reasons": attention_reasons,
            "requires_attention": len(attention_reasons) > 0
        })

    return {
        "total_students": len(candidates),
        "summary": attention_flags_summary,
        "students": results
    }

@router.get("/students/{id}/journey", summary="Get Complete Recruitment Journey & Timeline for Student")
def get_student_journey(
    id: int,
    ctx: TenantContext = Depends(require_role(OrgRole.ADMIN, OrgRole.MENTOR, OrgRole.COUNSELOR, OrgRole.RECRUITER)),
    db: Session = Depends(get_db)
):
    cand_query = db.query(Candidate).filter(
        Candidate.organization_id == ctx.organization.id,
        Candidate.id == id
    )
    role_str = ctx.role.value if hasattr(ctx.role, "value") else str(ctx.role).upper()
    if role_str == "MENTOR" and not ctx.user.is_superuser:
        cand_query = cand_query.filter(
            (Candidate.assigned_counselor_id == ctx.user.id) |
            (Candidate.assigned_recruiter_id == ctx.user.id) |
            (Candidate.user_id == ctx.user.id)
        )

    cand = cand_query.first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate student not found or access not permitted.")

    profile = db.query(StudentProfile).filter(StudentProfile.candidate_id == cand.id).first()
    resumes = db.query(Resume).filter(Resume.candidate_id == cand.id).order_by(Resume.id.desc()).all()
    apps = db.query(Application).filter(Application.candidate_id == cand.id).all()
    interactions = db.query(CandidateInteraction).filter(CandidateInteraction.candidate_id == cand.id).order_by(CandidateInteraction.id.desc()).all()

    # Build timeline events
    timeline = []

    for r in resumes:
        timeline.append({
            "timestamp": r.created_at.isoformat() if r.created_at else "",
            "category": "RESUME",
            "title": f"Uploaded Resume '{r.file_name}'",
            "detail": f"Quality Score: {r.quality_score}/100"
        })

    for app in apps:
        req_title = app.job_requirement.title if app.job_requirement else "Job Requirement"
        timeline.append({
            "timestamp": app.applied_at.isoformat() if app.applied_at else "",
            "category": "APPLICATION",
            "title": f"Applied for '{req_title}'",
            "detail": f"Stage: {app.stage.value if app.stage else 'APPLIED'}"
        })
        for iv in app.interviews:
            timeline.append({
                "timestamp": iv.scheduled_at.isoformat() if iv.scheduled_at else "",
                "category": "INTERVIEW",
                "title": f"Interview Scheduled: {iv.round_name}",
                "detail": f"Outcome: {iv.outcome.value if iv.outcome else 'SCHEDULED'}"
            })

    for i in interactions:
        timeline.append({
            "timestamp": i.interaction_at.isoformat() if i.interaction_at else "",
            "category": "HR_INTERACTION",
            "title": f"Contacted HR: {i.hr_name or 'HR'} at {i.company_name or 'Company'}",
            "detail": f"Outcome: {i.outcome}. Notes: {i.notes}"
        })

    timeline.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "candidate_id": cand.id,
        "full_name": cand.full_name,
        "email": cand.email,
        "completeness_score": profile.completeness_score if profile else 50,
        "timeline": timeline
    }
