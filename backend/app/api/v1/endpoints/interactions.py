from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.tenant import get_current_tenant, TenantContext
from app.models.candidate_interaction import CandidateInteraction
from app.models.activity import Call, CallType, CallOutcome, Followup, FollowupStatus, FollowupPriority, EntityType
from app.schemas.interaction import InteractionCreate, InteractionResponse
from app.api.v1.endpoints.profile import get_or_create_student_profile
from app.services.notification_service import create_notification

router = APIRouter()

@router.get("", response_model=List[InteractionResponse], summary="List Candidate HR Interactions")
def list_interactions(
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    candidate, _ = get_or_create_student_profile(db, ctx)
    interactions = db.query(CandidateInteraction).filter(
        CandidateInteraction.organization_id == ctx.organization.id,
        CandidateInteraction.candidate_id == candidate.id
    ).order_by(CandidateInteraction.id.desc()).all()

    return [InteractionResponse.model_validate(i) for i in interactions]

@router.post("", response_model=InteractionResponse, summary="Record HR Interaction & Create Next Move Followup")
def record_interaction(
    data: InteractionCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    candidate, _ = get_or_create_student_profile(db, ctx)

    interaction = CandidateInteraction(
        organization_id=ctx.organization.id,
        candidate_id=candidate.id,
        created_by_user_id=ctx.user.id,
        contact_id=data.contact_id,
        company_name=data.company_name or "Target Company",
        hr_name=data.hr_name or "HR Contact",
        interaction_type=data.interaction_type,
        outcome=data.outcome,
        notes=data.notes,
        next_move=data.next_move,
        due_date=data.due_date
    )
    db.add(interaction)
    db.flush()

    # Log Call in existing Call table for complete CRM compatibility
    call = Call(
        organization_id=ctx.organization.id,
        contact_id=data.contact_id,
        candidate_id=candidate.id,
        user_id=ctx.user.id,
        call_type=CallType.OUTBOUND if data.interaction_type == "CALL" else CallType.FOLLOWUP,
        outcome=CallOutcome.CONNECTED if data.outcome == "CONNECTED" else CallOutcome.RESUME_REQUESTED,
        notes=f"[{data.company_name or 'Company'}] HR Interaction: {data.notes}"
    )
    db.add(call)

    # Create Followup if Next Move is specified
    if data.next_move and data.due_date:
        followup = Followup(
            organization_id=ctx.organization.id,
            assigned_user_id=ctx.user.id,
            title=f"Next Move: {data.next_move} ({data.company_name or 'HR'})",
            description=f"Interaction notes: {data.notes}",
            due_date=data.due_date,
            status=FollowupStatus.PENDING,
            priority=FollowupPriority.HIGH,
            entity_type=EntityType.CONTACT if data.contact_id else None,
            entity_id=data.contact_id
        )
        db.add(followup)

    db.commit()
    db.refresh(interaction)

    # Trigger notification
    create_notification(
        db=db,
        organization_id=ctx.organization.id,
        user_id=ctx.user.id,
        title="HR Response Recorded",
        message=f"Recorded interaction with {data.hr_name or 'HR'} at {data.company_name or 'Company'}. Outcome: {data.outcome}.",
        notification_type="HR_RESPONSE",
        link_url="#/dashboard"
    )

    return InteractionResponse.model_validate(interaction)
