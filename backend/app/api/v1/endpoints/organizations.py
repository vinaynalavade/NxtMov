import secrets
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.tenant import get_current_tenant, get_current_user, TenantContext
from app.models.user import User
from app.models.organization import Organization, OrganizationMembership, OrgType, OrgRole, Invitation, InvitationStatus
from app.schemas.organization import (
    OrganizationCreate, OrganizationResponse, TeamMemberResponse,
    InvitationCreate, InvitationResponse, InvitationAccept
)

router = APIRouter()

@router.get("", response_model=List[OrganizationResponse], summary="List My Workspaces")
def list_my_workspaces(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    memberships = db.query(OrganizationMembership).filter(OrganizationMembership.user_id == user.id).all()
    org_responses = []
    for m in memberships:
        org = m.organization
        org_responses.append(OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            type=org.type,
            owner_id=org.owner_id,
            phone=org.phone,
            website=org.website,
            location=org.location,
            role_in_org=m.role,
            created_at=org.created_at
        ))
    return org_responses

@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED, summary="Create Consultancy Workspace")
def create_consultancy_organization(
    org_in: OrganizationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clean_slug = org_in.name.lower().replace(" ", "-") + "-" + secrets.token_hex(3)
    
    org = Organization(
        name=org_in.name,
        slug=clean_slug,
        type=org_in.type,
        owner_id=user.id,
        phone=org_in.phone,
        website=org_in.website,
        location=org_in.location
    )
    db.add(org)
    db.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role=OrgRole.ADMIN
    )
    db.add(membership)
    db.commit()
    db.refresh(org)

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        type=org.type,
        owner_id=org.owner_id,
        phone=org.phone,
        website=org.website,
        location=org.location,
        role_in_org=OrgRole.ADMIN,
        created_at=org.created_at
    )

@router.get("/team", response_model=List[TeamMemberResponse], summary="List Team Members")
def list_team_members(
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    memberships = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == ctx.organization.id
    ).all()

    team = []
    for m in memberships:
        u = m.user
        team.append(TeamMemberResponse(
            membership_id=m.id,
            user_id=u.id,
            full_name=u.full_name,
            email=u.email,
            role=m.role,
            joined_at=m.created_at
        ))
    return team

@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED, summary="Invite Team Member")
def invite_team_member(
    inv_in: InvitationCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    # RBAC Check: Only ADMIN can invite members
    if ctx.role != OrgRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Organization Admins can invite team members.")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    invitation = Invitation(
        organization_id=ctx.organization.id,
        email=inv_in.email,
        role=inv_in.role,
        token=token,
        status=InvitationStatus.PENDING,
        created_by_user_id=ctx.user.id,
        expires_at=expires_at
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    return invitation

@router.get("/invitations", response_model=List[InvitationResponse], summary="List Active Invitations")
def list_invitations(
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    return db.query(Invitation).filter(
        Invitation.organization_id == ctx.organization.id,
        Invitation.status == InvitationStatus.PENDING
    ).all()

@router.post("/invitations/accept", summary="Accept Organization Invitation")
def accept_invitation(
    accept_in: InvitationAccept,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    invitation = db.query(Invitation).filter(Invitation.token == accept_in.token).first()
    if not invitation or invitation.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or expired invitation token.")

    now = datetime.now(timezone.utc)
    if invitation.expires_at.tzinfo is None:
        inv_expires = invitation.expires_at.replace(tzinfo=timezone.utc)
    else:
        inv_expires = invitation.expires_at

    if inv_expires < now:
        invitation.status = InvitationStatus.EXPIRED
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation token has expired.")

    # Check if membership already exists
    existing = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == invitation.organization_id,
        OrganizationMembership.user_id == user.id
    ).first()

    if not existing:
        membership = OrganizationMembership(
            organization_id=invitation.organization_id,
            user_id=user.id,
            role=invitation.role
        )
        db.add(membership)

    invitation.status = InvitationStatus.ACCEPTED
    db.commit()

    return {"message": "Invitation accepted successfully!", "organization_id": invitation.organization_id}

@router.delete("/invitations/{invitation_id}", summary="Revoke Invitation")
def revoke_invitation(
    invitation_id: int,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    if ctx.role != OrgRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admins can revoke invitations.")

    invitation = db.query(Invitation).filter(
        Invitation.id == invitation_id,
        Invitation.organization_id == ctx.organization.id
    ).first()

    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found.")

    invitation.status = InvitationStatus.REVOKED
    db.commit()
    return {"message": "Invitation revoked successfully."}
