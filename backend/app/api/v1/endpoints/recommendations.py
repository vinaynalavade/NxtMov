import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.tenant import get_current_tenant, TenantContext
from app.models.requirement import JobRequirement, RequirementStatus
from app.models.application import Application
from app.models.job_recommendation import JobRecommendation
from app.schemas.job_recommendation import JobRecommendationResponse
from app.services.matching_service import calculate_match_score
from app.api.v1.endpoints.profile import get_or_create_student_profile

router = APIRouter()

@router.get("", response_model=List[JobRecommendationResponse], summary="Get Intelligent Role Recommendations for Candidate")
def get_recommendations(
    filter_type: Optional[str] = Query("ALL", alias="filter_type"),  # ALL, BEST_MATCHES, SAVED, APPLIED
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    candidate, profile = get_or_create_student_profile(db, ctx)

    # Get all active job requirements in the organization
    requirements = db.query(JobRequirement).filter(
        JobRequirement.organization_id == ctx.organization.id,
        JobRequirement.status.in_([RequirementStatus.OPEN, RequirementStatus.NEW])
    ).all()

    # Existing applications map
    applied_req_ids = set(
        app.job_requirement_id for app in db.query(Application).filter(
            Application.organization_id == ctx.organization.id,
            Application.candidate_id == candidate.id
        ).all()
    )

    # Saved & Dismissed recommendation state map
    rec_map = {
        rec.job_requirement_id: rec for rec in db.query(JobRecommendation).filter(
            JobRecommendation.organization_id == ctx.organization.id,
            JobRecommendation.candidate_id == candidate.id
        ).all()
    }

    output: List[JobRecommendationResponse] = []

    for req in requirements:
        rec_obj = rec_map.get(req.id)
        if rec_obj and rec_obj.is_dismissed and filter_type != "DISMISSED":
            continue

        match_info = calculate_match_score(candidate, req, profile)
        match_score = match_info["match_score"]

        # Persist or update JobRecommendation record
        if not rec_obj:
            rec_obj = JobRecommendation(
                organization_id=ctx.organization.id,
                candidate_id=candidate.id,
                job_requirement_id=req.id,
                match_score=match_score,
                score_breakdown_json=json.dumps(match_info),
                is_saved=False,
                is_dismissed=False
            )
            db.add(rec_obj)
            db.flush()
        else:
            rec_obj.match_score = match_score
            rec_obj.score_breakdown_json = json.dumps(match_info)

        is_applied = req.id in applied_req_ids

        # Filter check
        if filter_type == "BEST_MATCHES" and match_score < 75:
            continue
        if filter_type == "SAVED" and not rec_obj.is_saved:
            continue
        if filter_type == "APPLIED" and not is_applied:
            continue

        comp_name = req.company.name if req.company else "NxtMov Employer Partner"

        output.append(JobRecommendationResponse(
            id=rec_obj.id,
            candidate_id=candidate.id,
            job_requirement_id=req.id,
            title=req.title,
            company_name=comp_name,
            location=req.location,
            work_mode=req.work_mode.value if req.work_mode else "HYBRID",
            employment_type=req.employment_type.value if req.employment_type else "FULL_TIME",
            min_salary=float(req.min_salary) if req.min_salary else None,
            max_salary=float(req.max_salary) if req.max_salary else None,
            match_score=match_score,
            matched_skills=match_info["matched_skills"],
            missing_skills=match_info["missing_skills"],
            why_matches=match_info["why_matches"],
            what_is_missing=match_info["what_is_missing"],
            score_breakdown=match_info["breakdown"],
            is_saved=rec_obj.is_saved,
            is_dismissed=rec_obj.is_dismissed,
            is_applied=is_applied
        ))

    db.commit()

    # Sort output by match_score descending
    output.sort(key=lambda x: x.match_score, reverse=True)
    return output

@router.post("/{id}/save", summary="Save or Unsave Job Recommendation")
def toggle_save_recommendation(
    id: int,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    candidate, _ = get_or_create_student_profile(db, ctx)
    rec = db.query(JobRecommendation).filter(
        JobRecommendation.organization_id == ctx.organization.id,
        JobRecommendation.candidate_id == candidate.id,
        JobRecommendation.id == id
    ).first()

    if not rec:
        raise HTTPException(status_code=404, detail="Job recommendation not found.")

    rec.is_saved = not rec.is_saved
    db.commit()
    return {"id": rec.id, "is_saved": rec.is_saved, "message": "Saved preference updated."}

@router.post("/{id}/dismiss", summary="Dismiss Job Recommendation")
def dismiss_recommendation(
    id: int,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    candidate, _ = get_or_create_student_profile(db, ctx)
    rec = db.query(JobRecommendation).filter(
        JobRecommendation.organization_id == ctx.organization.id,
        JobRecommendation.candidate_id == candidate.id,
        JobRecommendation.id == id
    ).first()

    if not rec:
        raise HTTPException(status_code=404, detail="Job recommendation not found.")

    rec.is_dismissed = True
    db.commit()
    return {"id": rec.id, "is_dismissed": True, "message": "Recommendation dismissed."}
