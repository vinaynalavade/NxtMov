from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.core.database import get_db
from app.core.tenant import get_current_tenant, TenantContext
from app.models.candidate import Candidate, CandidateStatus, Document, DocumentType
from app.models.user import User
from app.models.application import Application, Submission
from app.schemas.candidate import (
    CandidateCreate, CandidateUpdate, CandidateAssign, CandidateResponse,
    DocumentCreate, DocumentResponse
)

router = APIRouter()

def _enrich_candidate_response(c: Candidate, db: Session) -> CandidateResponse:
    counselor_name = None
    recruiter_name = None
    if c.assigned_counselor_id:
        couns = db.query(User).filter(User.id == c.assigned_counselor_id).first()
        if couns:
            counselor_name = couns.full_name
    if c.assigned_recruiter_id:
        rec = db.query(User).filter(User.id == c.assigned_recruiter_id).first()
        if rec:
            recruiter_name = rec.full_name

    resp = CandidateResponse.model_validate(c)
    resp.counselor_name = counselor_name
    resp.recruiter_name = recruiter_name
    return resp

@router.get("", response_model=List[CandidateResponse], summary="List & Filter Candidates")
def list_candidates(
    search: Optional[str] = None,
    status_filter: Optional[CandidateStatus] = Query(None, alias="status"),
    skills_query: Optional[str] = Query(None, alias="skills"),
    min_exp: Optional[float] = None,
    max_exp: Optional[float] = None,
    assigned_counselor_id: Optional[int] = None,
    assigned_recruiter_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    query = db.query(Candidate).filter(Candidate.organization_id == ctx.organization.id)

    if status_filter:
        query = query.filter(Candidate.status == status_filter)

    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                Candidate.full_name.ilike(search_fmt),
                Candidate.email.ilike(search_fmt),
                Candidate.phone.ilike(search_fmt),
                Candidate.current_title.ilike(search_fmt),
                Candidate.current_company.ilike(search_fmt)
            )
        )

    if skills_query:
        s_fmt = f"%{skills_query}%"
        query = query.filter(
            or_(
                Candidate.primary_skills.ilike(s_fmt),
                Candidate.secondary_skills.ilike(s_fmt),
                Candidate.skills.ilike(s_fmt)
            )
        )

    if min_exp is not None:
        query = query.filter(Candidate.experience_years >= min_exp)
    if max_exp is not None:
        query = query.filter(Candidate.experience_years <= max_exp)

    if assigned_counselor_id:
        query = query.filter(Candidate.assigned_counselor_id == assigned_counselor_id)
    if assigned_recruiter_id:
        query = query.filter(Candidate.assigned_recruiter_id == assigned_recruiter_id)

    candidates = query.order_by(Candidate.id.desc()).offset(offset).limit(limit).all()
    return [_enrich_candidate_response(c, db) for c in candidates]

@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED, summary="Create Managed Candidate")
def create_candidate(
    cand_in: CandidateCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    existing = db.query(Candidate).filter(
        Candidate.organization_id == ctx.organization.id,
        Candidate.email == cand_in.email
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Candidate with this email already exists in workspace.")

    candidate = Candidate(
        organization_id=ctx.organization.id,
        **cand_in.model_dump()
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return _enrich_candidate_response(candidate, db)

@router.get("/{candidate_id}", response_model=CandidateResponse, summary="Get Candidate Detail")
def get_candidate(
    candidate_id: int,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        Candidate.organization_id == ctx.organization.id
    ).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")
    return _enrich_candidate_response(candidate, db)

@router.put("/{candidate_id}", response_model=CandidateResponse, summary="Update Candidate Profile")
def update_candidate(
    candidate_id: int,
    cand_in: CandidateUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        Candidate.organization_id == ctx.organization.id
    ).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    update_data = cand_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(candidate, field, val)

    db.commit()
    db.refresh(candidate)
    return _enrich_candidate_response(candidate, db)

@router.post("/{candidate_id}/assign", response_model=CandidateResponse, summary="Assign Counselor or Recruiter")
def assign_candidate(
    candidate_id: int,
    assign_in: CandidateAssign,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        Candidate.organization_id == ctx.organization.id
    ).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    if assign_in.assigned_counselor_id is not None:
        candidate.assigned_counselor_id = assign_in.assigned_counselor_id
    if assign_in.assigned_recruiter_id is not None:
        candidate.assigned_recruiter_id = assign_in.assigned_recruiter_id

    db.commit()
    db.refresh(candidate)
    return _enrich_candidate_response(candidate, db)

@router.get("/{candidate_id}/profile", summary="Get Complete Candidate 360 View")
def get_candidate_full_profile(
    candidate_id: int,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        Candidate.organization_id == ctx.organization.id
    ).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    applications = db.query(Application).filter(Application.candidate_id == candidate.id).all()
    submissions = db.query(Submission).filter(Submission.candidate_id == candidate.id).all()
    documents = db.query(Document).filter(Document.candidate_id == candidate.id).all()

    return {
        "candidate": _enrich_candidate_response(candidate, db),
        "applications_count": len(applications),
        # pyrefly: ignore [unknown-name]
        "submissions_count": lensubmissions if 'lensubmissions' in locals() else len(submissions),
        "submissions": [
            {
                "id": s.id,
                "requirement_title": s.job_requirement.title if s.job_requirement else "—",
                "company_name": s.job_requirement.company.name if s.job_requirement and s.job_requirement.company else "—",
                "status": s.status,
                "submitted_at": s.submitted_at
            } for s in submissions
        ],
        "documents": [DocumentResponse.model_validate(d) for d in documents]
    }

@router.post("/{candidate_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED, summary="Add Candidate Document")
def add_candidate_document(
    candidate_id: int,
    doc_in: DocumentCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        Candidate.organization_id == ctx.organization.id
    ).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    doc = Document(
        organization_id=ctx.organization.id,
        candidate_id=candidate.id,
        file_name=doc_in.file_name,
        file_type=doc_in.file_type,
        file_url=doc_in.file_url,
        doc_type=doc_in.doc_type
    )
    db.add(doc)
    
    if doc_in.doc_type == DocumentType.RESUME:
        candidate.resume_url = doc_in.file_url

    db.commit()
    db.refresh(doc)
    return doc

@router.get("/{candidate_id}/matches", summary="Get Requirement Matches for Candidate")
def get_candidate_job_matches(
    candidate_id: int,
    limit: int = Query(20, ge=1, le=100),
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    from app.models.requirement import JobRequirement
    from app.services.matching_service import calculate_candidate_match

    cand = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        Candidate.organization_id == ctx.organization.id
    ).first()

    if not cand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    requirements = db.query(JobRequirement).filter(JobRequirement.organization_id == ctx.organization.id).all()
    
    matches = []
    for req in requirements:
        match_info = calculate_candidate_match(cand, req)
        matches.append(match_info)

    matches.sort(key=lambda m: m["match_score"], reverse=True)
    return matches[:limit]
