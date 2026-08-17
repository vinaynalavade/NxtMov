from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr
from app.models.organization import OrgType, OrgRole, InvitationStatus

class OrganizationCreate(BaseModel):
    name: str
    type: OrgType = OrgType.CONSULTANCY
    phone: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None

class OrganizationResponse(BaseModel):
    id: int
    name: str
    slug: str
    type: OrgType
    owner_id: int
    phone: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    role_in_org: Optional[OrgRole] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TeamMemberResponse(BaseModel):
    membership_id: int
    user_id: int
    full_name: str
    email: str
    role: OrgRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InvitationCreate(BaseModel):
    email: EmailStr
    role: OrgRole = OrgRole.RECRUITER

class InvitationResponse(BaseModel):
    id: int
    organization_id: int
    email: str
    role: OrgRole
    token: str
    status: InvitationStatus
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InvitationAccept(BaseModel):
    token: str

class WorkspaceSwitchRequest(BaseModel):
    organization_id: int

class MemberRoleUpdateRequest(BaseModel):
    role: OrgRole
