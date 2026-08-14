from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class StudentProfileUpdate(BaseModel):
    avatar_url: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

    headline: Optional[str] = None
    career_objective: Optional[str] = None
    preferred_roles: Optional[str] = None
    preferred_locations: Optional[str] = None
    employment_preference: Optional[str] = None
    expected_salary: Optional[float] = None
    notice_period_days: Optional[int] = None

    highest_qualification: Optional[str] = None
    degree: Optional[str] = None
    college_university: Optional[str] = None
    graduation_year: Optional[int] = None
    specialization: Optional[str] = None
    cgpa_or_percentage: Optional[str] = None

    programming_languages: Optional[str] = None
    frameworks: Optional[str] = None
    testing_tools: Optional[str] = None
    databases: Optional[str] = None
    cloud_technologies: Optional[str] = None
    soft_skills: Optional[str] = None

    experience_json: Optional[str] = None
    projects_json: Optional[str] = None
    certifications_json: Optional[str] = None

    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    other_links_json: Optional[str] = None

    email_notifications_enabled: Optional[bool] = None
    job_alerts_enabled: Optional[bool] = None

class AccountSettingsUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    old_password: Optional[str] = None
    new_password: Optional[str] = None

class StudentProfileResponse(BaseModel):
    id: int
    candidate_id: int
    user_id: Optional[int] = None
    full_name: str
    email: str
    phone: Optional[str] = None

    avatar_url: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

    headline: Optional[str] = None
    career_objective: Optional[str] = None
    preferred_roles: Optional[str] = None
    preferred_locations: Optional[str] = None
    employment_preference: Optional[str] = None
    expected_salary: Optional[float] = None
    notice_period_days: Optional[int] = None

    highest_qualification: Optional[str] = None
    degree: Optional[str] = None
    college_university: Optional[str] = None
    graduation_year: Optional[int] = None
    specialization: Optional[str] = None
    cgpa_or_percentage: Optional[str] = None

    programming_languages: Optional[str] = None
    frameworks: Optional[str] = None
    testing_tools: Optional[str] = None
    databases: Optional[str] = None
    cloud_technologies: Optional[str] = None
    soft_skills: Optional[str] = None

    experience_json: Optional[str] = None
    projects_json: Optional[str] = None
    certifications_json: Optional[str] = None

    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    other_links_json: Optional[str] = None

    email_notifications_enabled: bool = True
    job_alerts_enabled: bool = True

    completeness_score: int = 0
    missing_items: List[str] = []

    class Config:
        from_attributes = True
