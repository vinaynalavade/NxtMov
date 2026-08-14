from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.tenant import get_current_tenant, TenantContext
from app.models.application import Application, ApplicationStage, Interview
from app.models.candidate import Candidate
from app.models.requirement import JobRequirement
from app.schemas.application import (
    ApplicationCreate, ApplicationUpdate, ApplicationResponse,
    InterviewCreate, InterviewResponse
)

router = APIRouter()

@router.get("", response_model=List[ApplicationResponse], summary="List Applications in Workspace")
def list_applications(
    stage: Optional[ApplicationStage] = Query(None, description="Filter by stage"),
    job_requirement_id: Optional[int] = Query(None, description="Filter by opportunity"),
    skip: int = 0,
    limit: int = 100,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    query = db.query(Application).filter(Application.organization_id == ctx.organization.id)
    if stage:
        query = query.filter(Application.stage == stage)
    if job_requirement_id:
        query = query.filter(Application.job_requirement_id == job_requirement_id)

    applications = query.order_by(Application.updated_at.desc()).offset(skip).limit(limit).all()
    return applications

@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED, summary="Create Job Application")
def create_application(
    app_in: ApplicationCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    # Verify requirement exists
    req = (
        db.query(JobRequirement)
        .filter(JobRequirement.id == app_in.job_requirement_id, JobRequirement.organization_id == ctx.organization.id)
        .first()
    )
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Requirement not found.")

    # Resolve candidate ID: Use provided candidate_id or fallback to user's personal candidate profile
    candidate_id = app_in.candidate_id
    if not candidate_id:
        cand = (
            db.query(Candidate)
            .filter(Candidate.organization_id == ctx.organization.id, Candidate.user_id == ctx.user.id)
            .first()
        )
        if not cand:
            # Fallback create
            cand = Candidate(
                organization_id=ctx.organization.id,
                user_id=ctx.user.id,
                full_name=ctx.user.full_name,
                email=ctx.user.email,
                phone=ctx.user.phone
            )
            db.add(cand)
            db.flush()
        candidate_id = cand.id

    # Check if application already exists for this requirement and candidate
    existing = (
        db.query(Application)
        .filter(
            Application.organization_id == ctx.organization.id,
            Application.job_requirement_id == app_in.job_requirement_id,
            Application.candidate_id == candidate_id
        )
        .first()
    )
    if existing:
        return existing

    app_obj = Application(
        organization_id=ctx.organization.id,
        job_requirement_id=app_in.job_requirement_id,
        candidate_id=candidate_id,
        stage=app_in.stage,
        notes=app_in.notes
    )
    db.add(app_obj)
    db.commit()
    db.refresh(app_obj)
    return app_obj

@router.put("/{application_id}", response_model=ApplicationResponse, summary="Update Application Stage")
def update_application(
    application_id: int,
    app_in: ApplicationUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    app_obj = (
        db.query(Application)
        .filter(Application.id == application_id, Application.organization_id == ctx.organization.id)
        .first()
    )
    if not app_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    update_data = app_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(app_obj, field, value)

    db.commit()
    db.refresh(app_obj)
    return app_obj

@router.post("/{application_id}/interviews", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED, summary="Schedule Interview Round")
def schedule_interview(
    application_id: int,
    interview_in: InterviewCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    app_obj = (
        db.query(Application)
        .filter(Application.id == application_id, Application.organization_id == ctx.organization.id)
        .first()
    )
    if not app_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    interview = Interview(
        application_id=app_obj.id,
        round_name=interview_in.round_name.strip(),
        scheduled_at=interview_in.scheduled_at,
        location_or_link=interview_in.location_or_link,
        interviewer_names=interview_in.interviewer_names,
        outcome=interview_in.outcome,
        feedback=interview_in.feedback
    )
    db.add(interview)

    # Auto update application stage to INTERVIEWING
    if app_obj.stage not in [ApplicationStage.INTERVIEWING, ApplicationStage.OFFERED, ApplicationStage.PLACED]:
        app_obj.stage = ApplicationStage.INTERVIEWING

    db.commit()
    db.refresh(interview)
    return interview
