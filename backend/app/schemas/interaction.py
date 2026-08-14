from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class InteractionCreate(BaseModel):
    contact_id: Optional[int] = None
    company_name: Optional[str] = None
    hr_name: Optional[str] = None
    interaction_type: str = "CALL"  # CALL, EMAIL, LINKEDIN, MESSAGE, INTERVIEW
    outcome: str = "CONNECTED"      # RESUME_REQUESTED, INTERVIEW_SCHEDULED, REQUIREMENT_CLOSED, CONNECTED, NO_ANSWER
    notes: str
    next_move: Optional[str] = None
    due_date: Optional[datetime] = None

class InteractionResponse(BaseModel):
    id: int
    candidate_id: int
    created_by_user_id: int
    contact_id: Optional[int] = None
    company_name: Optional[str] = None
    hr_name: Optional[str] = None
    interaction_type: str
    outcome: str
    notes: str
    next_move: Optional[str] = None
    due_date: Optional[datetime] = None
    interaction_at: datetime

    class Config:
        from_attributes = True
