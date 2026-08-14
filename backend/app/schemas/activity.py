from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.activity import CallType, CallOutcome, FollowupStatus, FollowupPriority, EntityType

# Call Schemas
class CallCreate(BaseModel):
    contact_id: Optional[int] = None
    candidate_id: Optional[int] = None
    call_type: CallType = CallType.OUTBOUND
    outcome: CallOutcome = CallOutcome.CONNECTED
    duration_minutes: Optional[int] = None
    notes: str
    
    # Auto Followup creation optional parameters
    create_followup: bool = False
    followup_title: Optional[str] = None
    followup_due_date: Optional[datetime] = None
    followup_priority: Optional[FollowupPriority] = FollowupPriority.MEDIUM
    followup_description: Optional[str] = None

class CallResponse(BaseModel):
    id: int
    organization_id: int
    user_id: int
    contact_id: Optional[int] = None
    candidate_id: Optional[int] = None
    call_type: CallType
    outcome: CallOutcome
    duration_minutes: Optional[int] = None
    notes: str
    called_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Follow-up Schemas
class FollowupCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: datetime
    priority: FollowupPriority = FollowupPriority.MEDIUM
    entity_type: Optional[EntityType] = None
    entity_id: Optional[int] = None

class FollowupUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[FollowupStatus] = None
    priority: Optional[FollowupPriority] = None

class FollowupResponse(BaseModel):
    id: int
    organization_id: int
    assigned_user_id: int
    title: str
    description: Optional[str] = None
    due_date: datetime
    status: FollowupStatus
    priority: FollowupPriority
    entity_type: Optional[EntityType] = None
    entity_id: Optional[int] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    # Extended CRM Contact Details
    contact_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

