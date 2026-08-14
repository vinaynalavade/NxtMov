from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class JobRecommendationResponse(BaseModel):
    id: int
    candidate_id: int
    job_requirement_id: int
    title: str
    company_name: str
    location: Optional[str] = None
    work_mode: str
    employment_type: str
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None

    match_score: float
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    why_matches: List[str] = []
    what_is_missing: List[str] = []
    score_breakdown: Dict[str, Any] = {}

    is_saved: bool = False
    is_dismissed: bool = False
    is_applied: bool = False
