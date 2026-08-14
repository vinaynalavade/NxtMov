from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.core.tenant import get_current_tenant, TenantContext
from app.models.requirement import JobRequirement, RequirementStatus
from app.schemas.requirement import JobRequirementCreate, JobRequirementUpdate, JobRequirementResponse

router = APIRouter()

@router.get("", response_model=List[JobRequirementResponse], summary="List Job Opportunities in Workspace")
def list_requirements(
    search: Optional[str] = Query(None, description="Search by job title, location, or skills"),
    status: Optional[RequirementStatus] = Query(None, description="Filter by status"),
    company_id: Optional[int] = Query(None, description="Filter by company"),
    skip: int = 0,
    limit: int = 100,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    query = db.query(JobRequirement).filter(JobRequirement.organization_id == ctx.organization.id)
    if company_id:
        query = query.filter(JobRequirement.company_id == company_id)
    if status:
        query = query.filter(JobRequirement.status == status)
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                JobRequirement.title.ilike(term),
                JobRequirement.location.ilike(term),
                JobRequirement.skills_req.ilike(term)
            )
        )
    requirements = query.order_by(JobRequirement.updated_at.desc()).offset(skip).limit(limit).all()
    return requirements

@router.post("", response_model=JobRequirementResponse, status_code=status.HTTP_201_CREATED, summary="Create Job Opportunity")
def create_requirement(
    req_in: JobRequirementCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    req = JobRequirement(
        organization_id=ctx.organization.id,
        company_id=req_in.company_id,
        contact_id=req_in.contact_id,
        title=req_in.title.strip(),
        description=req_in.description,
        location=req_in.location,
        experience_req=req_in.experience_req,
        skills_req=req_in.skills_req,
        employment_type=req_in.employment_type,
        source=req_in.source,
        openings_count=req_in.openings_count,
        min_salary=req_in.min_salary,
        max_salary=req_in.max_salary,
        status=req_in.status,
        notes=req_in.notes
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

@router.get("/{requirement_id}", response_model=JobRequirementResponse, summary="Get Job Opportunity Detail")
def get_requirement(
    requirement_id: int,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    req = (
        db.query(JobRequirement)
        .filter(JobRequirement.id == requirement_id, JobRequirement.organization_id == ctx.organization.id)
        .first()
    )
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Opportunity not found.")
    return req

@router.put("/{requirement_id}", response_model=JobRequirementResponse, summary="Update Job Opportunity")
def update_requirement(
    requirement_id: int,
    req_in: JobRequirementUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    req = (
        db.query(JobRequirement)
        .filter(JobRequirement.id == requirement_id, JobRequirement.organization_id == ctx.organization.id)
        .first()
    )
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Opportunity not found.")

    update_data = req_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(req, field, value)

    db.commit()
    db.refresh(req)
    return req

@router.delete("/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Job Opportunity")
def delete_requirement(
    requirement_id: int,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    req = (
        db.query(JobRequirement)
        .filter(JobRequirement.id == requirement_id, JobRequirement.organization_id == ctx.organization.id)
        .first()
    )
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Opportunity not found.")

    db.delete(req)
    db.commit()
    return None

@router.get("/{requirement_id}/matches", summary="Get Candidate Matches for Requirement")
def get_requirement_candidate_matches(
    requirement_id: int,
    min_score: float = Query(0.0, ge=0.0, le=100.0),
    limit: int = Query(20, ge=1, le=100),
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    from app.models.candidate import Candidate
    from app.services.matching_service import calculate_candidate_match

    req = db.query(JobRequirement).filter(
        JobRequirement.id == requirement_id,
        JobRequirement.organization_id == ctx.organization.id
    ).first()

    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Requirement not found.")

    candidates = db.query(Candidate).filter(Candidate.organization_id == ctx.organization.id).all()
    
    matches = []
    for cand in candidates:
        match_info = calculate_candidate_match(cand, req)
        if match_info["match_score"] >= min_score:
            matches.append(match_info)

    # Sort descending by match score
    matches.sort(key=lambda m: m["match_score"], reverse=True)
    return matches[:limit]
