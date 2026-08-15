from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class ResumeResponse(BaseModel):
    id: int
    candidate_id: int
    file_name: str
    file_type: str
    file_url: str
    file_size_bytes: int
    is_current: bool
    quality_score: int
    ats_score: Optional[int] = None
    career_domain: Optional[str] = None
    likely_roles: List[str] = []
    domain_explanation: Optional[str] = None
    score_breakdown: Optional[Dict[str, int]] = None
    strengths: List[str] = []
    improvements: List[str] = []
    warnings: List[str] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ResumeAnalysisResponse(BaseModel):
    id: int
    resume_id: int
    candidate_id: int
    parsed_data: Dict[str, Any]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ApplyAnalysisRequest(BaseModel):
    accept_fields: List[str] = []  # e.g. ["name", "email", "phone", "skills", "education", "linkedin_url", "github_url"]
