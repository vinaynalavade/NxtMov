from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.tenant import get_current_tenant, TenantContext
from app.core.permissions import require_permission, Permission
from app.models.application import Submission, SubmissionStatus, Placement, PlacementStatus
from app.models.candidate import Candidate, CandidateStatus
from app.models.requirement import JobRequirement
from app.models.company import Company
from app.models.user import User
from app.schemas.submission import (
    SubmissionCreate, SubmissionUpdate, SubmissionResponse,
    PlacementCreate, PlacementResponse
)

router = APIRouter()

def _enrich_submission(s: Submission, db: Session) -> SubmissionResponse:
    resp = SubmissionResponse.model_validate(s)
    if s.job_requirement:
        resp.job_title = s.job_requirement.title
        if s.job_requirement.company:
            resp.company_name = s.job_requirement.company.name
    if s.candidate:
        resp.candidate_name = s.candidate.full_name
    
    sub_user = db.query(User).filter(User.id == s.submitted_by_user_id).first()
    if sub_user:
        resp.submitted_by_name = sub_user.full_name
    return resp

@router.get("/submissions", response_model=List[SubmissionResponse], summary="List Candidates Submissions")
def list_submissions(
    job_requirement_id: Optional[int] = None,
    candidate_id: Optional[int] = None,
    status_filter: Optional[SubmissionStatus] = Query(None, alias="status"),
    ctx: TenantContext = Depends(require_permission(Permission.SUBMISSIONS_VIEW)),
    db: Session = Depends(get_db)
):
    query = db.query(Submission).filter(Submission.organization_id == ctx.organization.id)

    if job_requirement_id:
        query = query.filter(Submission.job_requirement_id == job_requirement_id)
    if candidate_id:
        query = query.filter(Submission.candidate_id == candidate_id)
    if status_filter:
        query = query.filter(Submission.status == status_filter)

    submissions = query.order_by(Submission.id.desc()).all()
    return [_enrich_submission(s, db) for s in submissions]

@router.post("/submissions", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED, summary="Submit Candidate for Requirement")
def create_submission(
    sub_in: SubmissionCreate,
    ctx: TenantContext = Depends(require_permission(Permission.SUBMISSIONS_MANAGE)),
    db: Session = Depends(get_db)
):
    req = db.query(JobRequirement).filter(
        JobRequirement.id == sub_in.job_requirement_id,
        JobRequirement.organization_id == ctx.organization.id
    ).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job requirement not found.")

    cand = db.query(Candidate).filter(
        Candidate.id == sub_in.candidate_id,
        Candidate.organization_id == ctx.organization.id
    ).first()
    if not cand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    existing = db.query(Submission).filter(
        Submission.organization_id == ctx.organization.id,
        Submission.job_requirement_id == sub_in.job_requirement_id,
        Submission.candidate_id == sub_in.candidate_id
    ).first()

    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Candidate has already been submitted for this requirement.")

    submission = Submission(
        organization_id=ctx.organization.id,
        job_requirement_id=sub_in.job_requirement_id,
        candidate_id=sub_in.candidate_id,
        submitted_by_user_id=ctx.user.id,
        status=SubmissionStatus.SUBMITTED,
        notes=sub_in.notes
    )
    db.add(submission)

    # Auto update candidate status to SUBMITTED if in NEW/SCREENING/READY
    if cand.status in [CandidateStatus.NEW, CandidateStatus.SCREENING, CandidateStatus.READY]:
        cand.status = CandidateStatus.SUBMITTED

    db.commit()
    db.refresh(submission)
    return _enrich_submission(submission, db)

@router.put("/submissions/{submission_id}", response_model=SubmissionResponse, summary="Update Submission Status")
def update_submission(
    submission_id: int,
    sub_in: SubmissionUpdate,
    ctx: TenantContext = Depends(require_permission(Permission.SUBMISSIONS_MANAGE)),
    db: Session = Depends(get_db)
):
    submission = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.organization_id == ctx.organization.id
    ).first()

    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found.")

    if sub_in.status:
        submission.status = sub_in.status
        # Sync candidate status if placed or interviewing
        if sub_in.status == SubmissionStatus.INTERVIEW:
            submission.candidate.status = CandidateStatus.INTERVIEWING
        elif sub_in.status == SubmissionStatus.OFFER:
            submission.candidate.status = CandidateStatus.OFFERED
        elif sub_in.status == SubmissionStatus.PLACED:
            submission.candidate.status = CandidateStatus.PLACED

    if sub_in.client_feedback is not None:
        submission.client_feedback = sub_in.client_feedback
    if sub_in.notes is not None:
        submission.notes = sub_in.notes

    db.commit()
    db.refresh(submission)
    return _enrich_submission(submission, db)

@router.get("/placements", response_model=List[PlacementResponse], summary="List Consultancy Placements")
def list_placements(
    ctx: TenantContext = Depends(require_permission(Permission.SUBMISSIONS_VIEW)),
    db: Session = Depends(get_db)
):
    placements = db.query(Placement).filter(Placement.organization_id == ctx.organization.id).order_by(Placement.id.desc()).all()
    resp_list = []
    for p in placements:
        cand = db.query(Candidate).filter(Candidate.id == p.candidate_id).first()
        comp = db.query(Company).filter(Company.id == p.company_id).first()
        req = db.query(JobRequirement).filter(JobRequirement.id == p.job_requirement_id).first()

        resp = PlacementResponse.model_validate(p)
        resp.candidate_name = cand.full_name if cand else "—"
        resp.company_name = comp.name if comp else "—"
        resp.job_title = req.title if req else "—"
        resp_list.append(resp)

    return resp_list

@router.post("/placements", response_model=PlacementResponse, status_code=status.HTTP_201_CREATED, summary="Record Placement")
def create_placement(
    place_in: PlacementCreate,
    ctx: TenantContext = Depends(require_permission(Permission.SUBMISSIONS_MANAGE)),
    db: Session = Depends(get_db)
):
    cand = db.query(Candidate).filter(
        Candidate.id == place_in.candidate_id,
        Candidate.organization_id == ctx.organization.id
    ).first()
    if not cand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    comp = db.query(Company).filter(
        Company.id == place_in.company_id,
        Company.organization_id == ctx.organization.id
    ).first()
    if not comp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")

    req = db.query(JobRequirement).filter(
        JobRequirement.id == place_in.job_requirement_id,
        JobRequirement.organization_id == ctx.organization.id
    ).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job requirement not found.")

    placement = Placement(
        organization_id=ctx.organization.id,
        candidate_id=place_in.candidate_id,
        job_requirement_id=place_in.job_requirement_id,
        company_id=place_in.company_id,
        join_date=place_in.join_date,
        offered_salary=place_in.offered_salary,
        billing_amount=place_in.billing_amount,
        recruiter_id=place_in.recruiter_id,
        counselor_id=place_in.counselor_id,
        status=place_in.status,
        notes=place_in.notes
    )
    db.add(placement)

    cand.status = CandidateStatus.PLACED

    db.commit()
    db.refresh(placement)

    resp = PlacementResponse.model_validate(placement)
    resp.candidate_name = cand.full_name
    resp.company_name = comp.name
    resp.job_title = req.title
    return resp
