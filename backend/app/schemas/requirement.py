from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.requirement import EmploymentType, RequirementStatus
from app.schemas.company import CompanyResponse
from app.schemas.contact import ContactResponse

class RequirementBase(BaseModel):
    company_id: int
    contact_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    experience_req: Optional[str] = None
    skills_req: Optional[str] = None
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    source: Optional[str] = None
    openings_count: int = 1
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    status: RequirementStatus = RequirementStatus.NEW
    notes: Optional[str] = None

class JobRequirementCreate(RequirementBase):
    pass

class JobRequirementUpdate(BaseModel):
    company_id: Optional[int] = None
    contact_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    experience_req: Optional[str] = None
    skills_req: Optional[str] = None
    employment_type: Optional[EmploymentType] = None
    source: Optional[str] = None
    openings_count: Optional[int] = None
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    status: Optional[RequirementStatus] = None
    notes: Optional[str] = None

class JobRequirementResponse(RequirementBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    company: Optional[CompanyResponse] = None
    contact: Optional[ContactResponse] = None

    model_config = ConfigDict(from_attributes=True)
