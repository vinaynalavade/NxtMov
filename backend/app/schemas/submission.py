from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.application import SubmissionStatus, PlacementStatus

class SubmissionCreate(BaseModel):
    job_requirement_id: int
    candidate_id: int
    notes: Optional[str] = None

class SubmissionUpdate(BaseModel):
    status: Optional[SubmissionStatus] = None
    client_feedback: Optional[str] = None
    notes: Optional[str] = None

class SubmissionResponse(BaseModel):
    id: int
    organization_id: int
    job_requirement_id: int
    candidate_id: int
    submitted_by_user_id: int
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    candidate_name: Optional[str] = None
    submitted_by_name: Optional[str] = None
    status: SubmissionStatus
    client_feedback: Optional[str] = None
    notes: Optional[str] = None
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PlacementCreate(BaseModel):
    candidate_id: int
    job_requirement_id: int
    company_id: int
    join_date: date
    offered_salary: Optional[float] = None
    billing_amount: Optional[float] = None
    recruiter_id: Optional[int] = None
    counselor_id: Optional[int] = None
    status: PlacementStatus = PlacementStatus.CONFIRMED
    notes: Optional[str] = None

class PlacementResponse(BaseModel):
    id: int
    organization_id: int
    candidate_id: int
    job_requirement_id: int
    company_id: int
    candidate_name: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    join_date: date
    offered_salary: Optional[float] = None
    billing_amount: Optional[float] = None
    status: PlacementStatus
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
