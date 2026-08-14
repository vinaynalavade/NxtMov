from datetime import datetime, date, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from app.core.database import get_db
from app.core.tenant import get_current_tenant, TenantContext
from app.models.activity import Call, Followup, FollowupStatus, CallOutcome, EntityType
from app.models.company import Contact, ContactStatus
from app.models.requirement import JobRequirement, RequirementStatus
from app.models.application import Application, ApplicationStage, Interview, InterviewOutcome
from app.schemas.activity import (
    CallCreate, CallResponse,
    FollowupCreate, FollowupUpdate, FollowupResponse
)

router = APIRouter()

def _enrich_followup(f: Followup, db: Session) -> FollowupResponse:
    resp = FollowupResponse.model_validate(f)
    if f.entity_type == EntityType.CONTACT and f.entity_id:
        from app.models.company import Company
        contact = db.query(Contact).filter(Contact.id == f.entity_id, Contact.organization_id == f.organization_id).first()
        if contact:
            resp.contact_name = contact.name
            resp.phone = contact.phone
            resp.email = contact.email
            if contact.company:
                resp.company_name = contact.company.name
            elif contact.company_id:
                comp = db.query(Company).filter(Company.id == contact.company_id).first()
                if comp:
                    resp.company_name = comp.name
    return resp

# --- CALL LOGGING ---

@router.post("/calls", response_model=CallResponse, status_code=status.HTTP_201_CREATED, summary="Log HR Call")
def log_call(
    call_in: CallCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    # Verify contact belongs to tenant if contact_id provided
    if call_in.contact_id:
        contact = (
            db.query(Contact)
            .filter(Contact.id == call_in.contact_id, Contact.organization_id == ctx.organization.id)
            .first()
        )
        if not contact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found.")
        
        # Update contact status based on call outcome
        if call_in.outcome == CallOutcome.OPPORTUNITY_AVAILABLE:
            contact.status = ContactStatus.OPPORTUNITY_AVAILABLE
        elif call_in.outcome == CallOutcome.RESUME_REQUESTED:
            contact.status = ContactStatus.INTERESTED
        elif call_in.outcome == CallOutcome.NOT_RELEVANT:
            contact.status = ContactStatus.NOT_RELEVANT
        elif contact.status == ContactStatus.NOT_CONTACTED:
            contact.status = ContactStatus.CONTACTED

    call = Call(
        organization_id=ctx.organization.id,
        user_id=ctx.user.id,
        contact_id=call_in.contact_id,
        candidate_id=call_in.candidate_id,
        call_type=call_in.call_type,
        outcome=call_in.outcome,
        duration_minutes=call_in.duration_minutes,
        notes=call_in.notes
    )
    db.add(call)
    db.flush()

    # Create optional Follow-up task ("Next Move")
    if call_in.create_followup and call_in.followup_due_date:
        followup_title = call_in.followup_title or f"Follow up call: {call_in.outcome.value}"
        desc = call_in.followup_description or f"Follow-up from call log on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}. Notes: {call_in.notes}"
        priority = call_in.followup_priority or FollowupPriority.MEDIUM
        followup = Followup(
            organization_id=ctx.organization.id,
            assigned_user_id=ctx.user.id,
            title=followup_title,
            description=desc,
            due_date=call_in.followup_due_date,
            priority=priority,
            status=FollowupStatus.PENDING,
            entity_type=EntityType.CONTACT if call_in.contact_id else None,
            entity_id=call_in.contact_id
        )
        db.add(followup)

    db.commit()
    db.refresh(call)
    return call

@router.get("/calls", response_model=List[CallResponse], summary="List Call Logs")
def list_calls(
    contact_id: Optional[int] = Query(None, description="Filter by HR contact"),
    skip: int = 0,
    limit: int = 100,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    query = db.query(Call).filter(Call.organization_id == ctx.organization.id)
    if contact_id:
        query = query.filter(Call.contact_id == contact_id)
    calls = query.order_by(Call.called_at.desc()).offset(skip).limit(limit).all()
    return calls

# --- FOLLOW-UPS / NEXT MOVE ENGINE ---

@router.post("/followups", response_model=FollowupResponse, status_code=status.HTTP_201_CREATED, summary="Create Follow-up Task")
def create_followup(
    followup_in: FollowupCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    followup = Followup(
        organization_id=ctx.organization.id,
        assigned_user_id=ctx.user.id,
        title=followup_in.title,
        description=followup_in.description,
        due_date=followup_in.due_date,
        priority=followup_in.priority,
        entity_type=followup_in.entity_type,
        entity_id=followup_in.entity_id,
        status=FollowupStatus.PENDING
    )
    db.add(followup)
    db.commit()
    db.refresh(followup)
    return _enrich_followup(followup, db)

@router.get("/followups", response_model=List[FollowupResponse], summary="List Follow-ups (Next Moves)")
def list_followups(
    filter_type: str = Query("all", description="Filter by: all, today, overdue, upcoming, completed"),
    skip: int = 0,
    limit: int = 100,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    now_utc = datetime.now(timezone.utc)
    today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now_utc.replace(hour=23, minute=59, second=59, microsecond=999999)

    query = db.query(Followup).filter(Followup.organization_id == ctx.organization.id)

    if filter_type == "today":
        query = query.filter(
            Followup.status == FollowupStatus.PENDING,
            Followup.due_date >= today_start,
            Followup.due_date <= today_end
        )
    elif filter_type == "overdue":
        query = query.filter(
            Followup.status == FollowupStatus.PENDING,
            Followup.due_date < today_start
        )
    elif filter_type == "upcoming":
        query = query.filter(
            Followup.status == FollowupStatus.PENDING,
            Followup.due_date > today_end
        )
    elif filter_type == "completed":
        query = query.filter(Followup.status == FollowupStatus.COMPLETED)
    else:
        # Default pending items first
        query = query.filter(Followup.status == FollowupStatus.PENDING)

    followups = query.order_by(Followup.due_date.asc()).offset(skip).limit(limit).all()
    return [_enrich_followup(f, db) for f in followups]

@router.put("/followups/{followup_id}", response_model=FollowupResponse, summary="Update / Complete Follow-up Task")
def update_followup(
    followup_id: int,
    followup_in: FollowupUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    followup = (
        db.query(Followup)
        .filter(Followup.id == followup_id, Followup.organization_id == ctx.organization.id)
        .first()
    )
    if not followup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up task not found.")

    update_data = followup_in.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] == FollowupStatus.COMPLETED and followup.status != FollowupStatus.COMPLETED:
        followup.completed_at = datetime.now(timezone.utc)
    elif "status" in update_data and update_data["status"] == FollowupStatus.PENDING:
        followup.completed_at = None

    for field, value in update_data.items():
        setattr(followup, field, value)

    db.commit()
    db.refresh(followup)
    return followup

# --- DASHBOARD STATS ---

@router.get("/dashboard/stats", summary="Get Dashboard KPIs & Today's Next Moves")
def get_dashboard_stats(
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    now_utc = datetime.now(timezone.utc)
    today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now_utc.replace(hour=23, minute=59, second=59, microsecond=999999)

    # 1. Followups due today
    today_followups_count = (
        db.query(Followup)
        .filter(
            Followup.organization_id == ctx.organization.id,
            Followup.status == FollowupStatus.PENDING,
            Followup.due_date >= today_start,
            Followup.due_date <= today_end
        )
        .count()
    )

    # 2. Overdue followups count
    overdue_count = (
        db.query(Followup)
        .filter(
            Followup.organization_id == ctx.organization.id,
            Followup.status == FollowupStatus.PENDING,
            Followup.due_date < today_start
        )
        .count()
    )

    # 3. Active Opportunities count
    opportunities_count = (
        db.query(JobRequirement)
        .filter(
            JobRequirement.organization_id == ctx.organization.id,
            JobRequirement.status.in_([RequirementStatus.NEW, RequirementStatus.INTERESTED, RequirementStatus.APPLIED, RequirementStatus.INTERVIEWING])
        )
        .count()
    )

    # 4. Total Applications
    applications_count = (
        db.query(Application)
        .filter(Application.organization_id == ctx.organization.id)
        .count()
    )

    # 5. Scheduled Interviews count
    interviews_count = (
        db.query(Interview)
        .join(Application)
        .filter(
            Application.organization_id == ctx.organization.id,
            Interview.outcome == InterviewOutcome.SCHEDULED
        )
        .count()
    )

    # Fetch top pending followups for today/overdue
    pending_followups = (
        db.query(Followup)
        .filter(
            Followup.organization_id == ctx.organization.id,
            Followup.status == FollowupStatus.PENDING,
            Followup.due_date <= today_end
        )
        .order_by(Followup.due_date.asc())
        .limit(10)
        .all()
    )

    # 6. Consultancy Specific Metrics
    from app.models.candidate import Candidate
    from app.models.application import Submission, Placement
    from app.models.organization import OrgType

    open_requirements_count = (
        db.query(JobRequirement)
        .filter(
            JobRequirement.organization_id == ctx.organization.id,
            JobRequirement.status == RequirementStatus.OPEN
        )
        .count()
    )

    active_candidates_count = (
        db.query(Candidate)
        .filter(Candidate.organization_id == ctx.organization.id)
        .count()
    )

    submissions_count = (
        db.query(Submission)
        .filter(Submission.organization_id == ctx.organization.id)
        .count()
    )

    placements_count = (
        db.query(Placement)
        .filter(Placement.organization_id == ctx.organization.id)
        .count()
    )

    return {
        "org_type": ctx.organization.type,
        "followups_due_today": today_followups_count,
        "overdue_followups": overdue_count,
        "active_opportunities": opportunities_count,
        "applications_count": applications_count,
        "interviews_count": interviews_count,
        # Consultancy Stats
        "open_requirements": open_requirements_count,
        "active_candidates": active_candidates_count,
        "submissions_count": submissions_count,
        "placements_count": placements_count,
        "today_followups": [_enrich_followup(f, db) for f in pending_followups]
    }

