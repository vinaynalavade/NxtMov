from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.application import ApplicationStage, InterviewOutcome, OfferStatus, PlacementStatus
from app.schemas.requirement import JobRequirementResponse

# Interview Schemas
class InterviewCreate(BaseModel):
    round_name: str
    scheduled_at: datetime
    location_or_link: Optional[str] = None
    interviewer_names: Optional[str] = None
    outcome: InterviewOutcome = InterviewOutcome.SCHEDULED
    feedback: Optional[str] = None

class InterviewResponse(BaseModel):
    id: int
    application_id: int
    round_name: str
    scheduled_at: datetime
    location_or_link: Optional[str] = None
    interviewer_names: Optional[str] = None
    outcome: InterviewOutcome
    feedback: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Application Schemas
class ApplicationCreate(BaseModel):
    job_requirement_id: int
    candidate_id: Optional[int] = None # Auto-resolved to individual candidate if not specified
    stage: ApplicationStage = ApplicationStage.APPLIED
    notes: Optional[str] = None

class ApplicationUpdate(BaseModel):
    stage: Optional[ApplicationStage] = None
    notes: Optional[str] = None

class ApplicationResponse(BaseModel):
    id: int
    organization_id: int
    job_requirement_id: int
    candidate_id: int
    stage: ApplicationStage
    notes: Optional[str] = None
    applied_at: datetime
    updated_at: datetime
    job_requirement: Optional[JobRequirementResponse] = None
    interviews: List[InterviewResponse] = []

    model_config = ConfigDict(from_attributes=True)
