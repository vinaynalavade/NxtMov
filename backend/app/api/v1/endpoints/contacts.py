from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.core.tenant import get_current_tenant, TenantContext
from app.core.permissions import require_permission, Permission
from app.models.company import Company, Contact, ContactStatus
from app.models.activity import Call, Followup, FollowupStatus, EntityType
from app.models.requirement import JobRequirement, RequirementStatus
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse

router = APIRouter()

def _enrich_contact(contact: Contact, db: Session) -> ContactResponse:
    # 1. Last call
    last_call = (
        db.query(Call)
        .filter(Call.organization_id == contact.organization_id, Call.contact_id == contact.id)
        .order_by(Call.called_at.desc())
        .first()
    )
    last_call_at = last_call.called_at if last_call else None
    last_call_outcome = last_call.outcome.value if last_call else None

    # 2. Next followup
    next_fup = (
        db.query(Followup)
        .filter(
            Followup.organization_id == contact.organization_id,
            Followup.entity_type == EntityType.CONTACT,
            Followup.entity_id == contact.id,
            Followup.status == FollowupStatus.PENDING
        )
        .order_by(Followup.due_date.asc())
        .first()
    )
    next_followup_date = next_fup.due_date if next_fup else None
    next_followup_title = next_fup.title if next_fup else None

    # 3. Total calls count
    total_calls_count = (
        db.query(Call)
        .filter(Call.organization_id == contact.organization_id, Call.contact_id == contact.id)
        .count()
    )

    # 4. Active opportunities count
    opp_filter = [JobRequirement.organization_id == contact.organization_id]
    if contact.company_id:
        opp_filter.append(or_(JobRequirement.contact_id == contact.id, JobRequirement.company_id == contact.company_id))
    else:
        opp_filter.append(JobRequirement.contact_id == contact.id)

    opp_filter.append(JobRequirement.status.in_([
        RequirementStatus.OPEN, RequirementStatus.NEW, RequirementStatus.INTERESTED,
        RequirementStatus.APPLIED, RequirementStatus.INTERVIEWING, RequirementStatus.OFFER
    ]))

    active_opps_count = db.query(JobRequirement).filter(*opp_filter).count()

    resp = ContactResponse.model_validate(contact)
    resp.last_call_at = last_call_at
    resp.last_call_outcome = last_call_outcome
    resp.next_followup_date = next_followup_date
    resp.next_followup_title = next_followup_title
    resp.total_calls_count = total_calls_count
    resp.active_opportunities_count = active_opps_count
    return resp

@router.get("", response_model=List[ContactResponse], summary="List HR Contacts in Workspace")
def list_contacts(
    search: Optional[str] = Query(None, description="Search by name, email, phone, designation, or location"),
    status: Optional[ContactStatus] = Query(None, description="Filter by contact status"),
    company_id: Optional[int] = Query(None, description="Filter by company"),
    has_followup: Optional[bool] = Query(None, description="Filter contacts with pending follow-up"),
    has_opportunity: Optional[bool] = Query(None, description="Filter contacts with active opportunities"),
    skip: int = 0,
    limit: int = 100,
    ctx: TenantContext = Depends(require_permission(Permission.CONTACTS_VIEW)),
    db: Session = Depends(get_db)
):
    query = db.query(Contact).filter(Contact.organization_id == ctx.organization.id)

    if company_id:
        query = query.filter(Contact.company_id == company_id)

    if status:
        query = query.filter(Contact.status == status)

    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Contact.name.ilike(term),
                Contact.email.ilike(term),
                Contact.phone.ilike(term),
                Contact.designation.ilike(term),
                Contact.location.ilike(term)
            )
        )

    contacts = query.order_by(Contact.updated_at.desc()).offset(skip).limit(limit).all()
    enriched = [_enrich_contact(c, db) for c in contacts]

    if has_followup is True:
        enriched = [c for c in enriched if c.next_followup_date is not None]
    elif has_followup is False:
        enriched = [c for c in enriched if c.next_followup_date is None]

    if has_opportunity is True:
        enriched = [c for c in enriched if c.active_opportunities_count > 0]
    elif has_opportunity is False:
        enriched = [c for c in enriched if c.active_opportunities_count == 0]

    return enriched

@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED, summary="Create HR Contact")
def create_contact(
    contact_in: ContactCreate,
    ctx: TenantContext = Depends(require_permission(Permission.CONTACTS_MANAGE)),
    db: Session = Depends(get_db)
):
    company_id = contact_in.company_id
    if not company_id and contact_in.company_name:
        company_name_clean = contact_in.company_name.strip()
        existing_company = (
            db.query(Company)
            .filter(
                Company.organization_id == ctx.organization.id,
                Company.name.ilike(company_name_clean)
            )
            .first()
        )
        if existing_company:
            company_id = existing_company.id
        else:
            new_company = Company(
                organization_id=ctx.organization.id,
                name=company_name_clean
            )
            db.add(new_company)
            db.flush()
            company_id = new_company.id

    contact = Contact(
        organization_id=ctx.organization.id,
        company_id=company_id,
        name=contact_in.name.strip(),
        designation=contact_in.designation,
        phone=contact_in.phone,
        email=contact_in.email,
        linkedin_url=contact_in.linkedin_url,
        location=contact_in.location,
        source=contact_in.source,
        status=contact_in.status,
        notes=contact_in.notes
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return _enrich_contact(contact, db)

@router.get("/{contact_id}", response_model=ContactResponse, summary="Get Contact Detail")
def get_contact(
    contact_id: int,
    ctx: TenantContext = Depends(require_permission(Permission.CONTACTS_VIEW)),
    db: Session = Depends(get_db)
):
    contact = (
        db.query(Contact)
        .filter(Contact.id == contact_id, Contact.organization_id == ctx.organization.id)
        .first()
    )
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HR Contact not found.")
    return _enrich_contact(contact, db)

@router.get("/{contact_id}/timeline", summary="Get Contact 360 View & Timeline")
def get_contact_timeline(
    contact_id: int,
    ctx: TenantContext = Depends(require_permission(Permission.CONTACTS_VIEW)),
    db: Session = Depends(get_db)
):
    contact = (
        db.query(Contact)
        .filter(Contact.id == contact_id, Contact.organization_id == ctx.organization.id)
        .first()
    )
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HR Contact not found.")

    calls = (
        db.query(Call)
        .filter(Call.organization_id == ctx.organization.id, Call.contact_id == contact_id)
        .order_by(Call.called_at.desc())
        .all()
    )

    followups = (
        db.query(Followup)
        .filter(
            Followup.organization_id == ctx.organization.id,
            Followup.entity_type == EntityType.CONTACT,
            Followup.entity_id == contact_id
        )
        .order_by(Followup.due_date.desc())
        .all()
    )

    opp_filter = [JobRequirement.organization_id == ctx.organization.id]
    if contact.company_id:
        opp_filter.append(or_(JobRequirement.contact_id == contact_id, JobRequirement.company_id == contact.company_id))
    else:
        opp_filter.append(JobRequirement.contact_id == contact_id)

    opportunities = (
        db.query(JobRequirement)
        .filter(*opp_filter)
        .order_by(JobRequirement.created_at.desc())
        .all()
    )

    timeline_events = []

    for c in calls:
        timeline_events.append({
            "type": "CALL",
            "timestamp": c.called_at,
            "title": f"ðŸ“ž Call ({c.call_type.value})",
            "outcome": c.outcome.value,
            "notes": c.notes,
            "duration": c.duration_minutes,
            "id": c.id
        })

    for f in followups:
        timeline_events.append({
            "type": "FOLLOWUP",
            "timestamp": f.due_date,
            "title": f"âš¡ Next Move: {f.title}",
            "status": f.status.value,
            "priority": f.priority.value,
            "description": f.description,
            "completed_at": f.completed_at,
            "id": f.id
        })

    for o in opportunities:
        timeline_events.append({
            "type": "OPPORTUNITY",
            "timestamp": o.created_at,
            "title": f"ðŸ’¼ Opportunity: {o.title}",
            "status": o.status.value,
            "location": o.location,
            "employment_type": o.employment_type.value,
            "id": o.id
        })

    timeline_events.sort(key=lambda x: x["timestamp"] if x["timestamp"] else datetime.min, reverse=True)

    enriched_contact = _enrich_contact(contact, db)

    return {
        "contact": enriched_contact,
        "calls": calls,
        "followups": followups,
        "opportunities": opportunities,
        "timeline": timeline_events
    }

@router.put("/{contact_id}", response_model=ContactResponse, summary="Update HR Contact")
def update_contact(
    contact_id: int,
    contact_in: ContactUpdate,
    ctx: TenantContext = Depends(require_permission(Permission.CONTACTS_MANAGE)),
    db: Session = Depends(get_db)
):
    contact = (
        db.query(Contact)
        .filter(Contact.id == contact_id, Contact.organization_id == ctx.organization.id)
        .first()
    )
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HR Contact not found.")

    update_data = contact_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)
    return _enrich_contact(contact, db)

@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete HR Contact")
def delete_contact(
    contact_id: int,
    ctx: TenantContext = Depends(require_permission(Permission.CONTACTS_MANAGE)),
    db: Session = Depends(get_db)
):
    contact = (
        db.query(Contact)
        .filter(Contact.id == contact_id, Contact.organization_id == ctx.organization.id)
        .first()
    )
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HR Contact not found.")

    db.delete(contact)
    db.commit()
    return None
