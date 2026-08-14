from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr
from app.models.candidate import CandidateStatus, DocumentType

class CandidateCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    experience_years: Optional[float] = None
    notice_period_days: Optional[int] = None
    current_salary: Optional[float] = None
    expected_salary: Optional[float] = None
    primary_skills: Optional[str] = None
    secondary_skills: Optional[str] = None
    skills: Optional[str] = None
    source: Optional[str] = None
    resume_url: Optional[str] = None
    status: CandidateStatus = CandidateStatus.NEW
    assigned_counselor_id: Optional[int] = None
    assigned_recruiter_id: Optional[int] = None
    notes: Optional[str] = None

class CandidateUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    experience_years: Optional[float] = None
    notice_period_days: Optional[int] = None
    current_salary: Optional[float] = None
    expected_salary: Optional[float] = None
    primary_skills: Optional[str] = None
    secondary_skills: Optional[str] = None
    skills: Optional[str] = None
    source: Optional[str] = None
    resume_url: Optional[str] = None
    status: Optional[CandidateStatus] = None
    assigned_counselor_id: Optional[int] = None
    assigned_recruiter_id: Optional[int] = None
    notes: Optional[str] = None

class CandidateAssign(BaseModel):
    assigned_counselor_id: Optional[int] = None
    assigned_recruiter_id: Optional[int] = None

class DocumentCreate(BaseModel):
    file_name: str
    file_type: str
    file_url: str
    doc_type: DocumentType = DocumentType.RESUME

class DocumentResponse(BaseModel):
    id: int
    candidate_id: int
    file_name: str
    file_type: str
    file_url: str
    doc_type: DocumentType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CandidateResponse(BaseModel):
    id: int
    organization_id: int
    user_id: Optional[int] = None
    full_name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    experience_years: Optional[float] = None
    notice_period_days: Optional[int] = None
    current_salary: Optional[float] = None
    expected_salary: Optional[float] = None
    primary_skills: Optional[str] = None
    secondary_skills: Optional[str] = None
    skills: Optional[str] = None
    source: Optional[str] = None
    resume_url: Optional[str] = None
    status: CandidateStatus
    assigned_counselor_id: Optional[int] = None
    assigned_recruiter_id: Optional[int] = None
    counselor_name: Optional[str] = None
    recruiter_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
