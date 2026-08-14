from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.company import ContactStatus
from app.schemas.company import CompanyResponse

class ContactBase(BaseModel):
    name: str
    designation: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None
    status: ContactStatus = ContactStatus.NOT_CONTACTED
    notes: Optional[str] = None
    company_id: Optional[int] = None

class ContactCreate(ContactBase):
    company_name: Optional[str] = None  # Quick company creation if ID not specified

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None
    status: Optional[ContactStatus] = None
    notes: Optional[str] = None
    company_id: Optional[int] = None

class ContactResponse(ContactBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    company: Optional[CompanyResponse] = None
    
    # Enhanced CRM summary fields
    last_call_at: Optional[datetime] = None
    last_call_outcome: Optional[str] = None
    next_followup_date: Optional[datetime] = None
    next_followup_title: Optional[str] = None
    active_opportunities_count: int = 0
    total_calls_count: int = 0

    model_config = ConfigDict(from_attributes=True)

