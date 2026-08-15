import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, field_validator, ValidationInfo

def validate_name_field(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    val = v.strip()
    if not val:
        return None
    if len(val) < 2 or len(val) > 80:
        raise ValueError("Full name must be between 2 and 80 characters.")
    if any(ch.isdigit() for ch in val) or "@" in val or "http://" in val or "https://" in val:
        raise ValueError("Full name can contain letters, spaces, hyphens, and apostrophes only.")
    return re.sub(r"\s+", " ", val)

def validate_email_field(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    val = v.strip().lower()
    if not val:
        return None
    if val == "demo@nxtmov.local":
        return val
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", val):
        raise ValueError("Please enter a valid email address with a valid domain.")
    return val

def validate_phone_field(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    val = v.strip()
    if not val:
        return None
    digits = re.sub(r"\D", "", val)
    if len(digits) < 7 or len(digits) > 15:
        raise ValueError("Please enter a valid mobile number (7 to 15 digits).")
    return val

def validate_url_field(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    val = v.strip()
    if not val:
        return None
    if not (val.startswith("http://") or val.startswith("https://") or "linkedin.com" in val or "github.com" in val):
        raise ValueError("Please enter a valid URL (starting with https:// or http://).")
    return val

def validate_location_field(v: Optional[str], field_name: str = "Location") -> Optional[str]:
    if v is None:
        return None
    val = v.strip()
    if not val:
        return None
    if len(val) > 100:
        raise ValueError(f"{field_name} cannot exceed 100 characters.")
    if "@" in val or "http://" in val or "https://" in val:
        raise ValueError(f"{field_name} must be a valid geographic location name.")
    if not any(c.isalpha() for c in val):
        raise ValueError(f"{field_name} must contain valid geographic text.")
    return re.sub(r"\s+", " ", val)

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

    @field_validator("city", "state", "country")
    @classmethod
    def check_locations(cls, v, info: ValidationInfo):
        return validate_location_field(v, info.field_name.capitalize() if info and info.field_name else "Location")

    @field_validator("linkedin_url", "github_url", "portfolio_url")
    @classmethod
    def check_urls(cls, v):
        return validate_url_field(v)

    @field_validator("graduation_year")
    @classmethod
    def check_year(cls, v):
        if v is not None and (v < 1960 or v > 2035):
            raise ValueError("Graduation year must be a realistic year between 1960 and 2035.")
        return v

    @field_validator("expected_salary")
    @classmethod
    def check_salary(cls, v):
        if v is not None and (v < 0 or v > 100000000):
            raise ValueError("Expected salary cannot be negative or exceed sensible limits.")
        return v

    @field_validator("notice_period_days")
    @classmethod
    def check_notice(cls, v):
        if v is not None and (v < 0 or v > 365):
            raise ValueError("Notice period must be between 0 and 365 days.")
        return v

class AccountSettingsUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    old_password: Optional[str] = None
    new_password: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def check_name(cls, v):
        return validate_name_field(v)

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        return validate_email_field(v)

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v):
        return validate_phone_field(v)

    @field_validator("new_password")
    @classmethod
    def check_pwd(cls, v):
        if v is not None and len(v) < 6:
            raise ValueError("New password must be at least 6 characters.")
        return v

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

    is_email_verified: bool = False
    is_phone_verified: bool = False

    model_config = ConfigDict(from_attributes=True)
