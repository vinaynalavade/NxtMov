from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ResumeResponse(BaseModel):
    id: int
    candidate_id: int
    file_name: str
    file_type: str
    file_url: str
    file_size_bytes: int
    is_current: bool
    quality_score: int
    strengths: List[str] = []
    improvements: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True

class ResumeAnalysisResponse(BaseModel):
    id: int
    resume_id: int
    candidate_id: int
    parsed_data: Dict[str, Any]
    status: str
    created_at: datetime

class ApplyAnalysisRequest(BaseModel):
    accept_fields: List[str] = []  # e.g. ["name", "email", "phone", "skills", "education", "linkedin_url"]
