import enum
from typing import Optional, Any
from sqlalchemy import String, Text, ForeignKey, Integer, Float, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class StudentProfile(Base, TimestampMixin):
    __tablename__ = "student_profiles"
    __table_args__ = (
        Index("ix_student_profiles_cand_user", "candidate_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)

    # Personal Information
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default="India")

    # Professional Information
    headline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    career_objective: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_roles: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Comma or JSON string
    preferred_locations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Comma or JSON string
    employment_preference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="FULL_TIME")
    expected_salary: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notice_period_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Education
    highest_qualification: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    degree: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    college_university: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    graduation_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    specialization: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    cgpa_or_percentage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Skills Breakdown
    programming_languages: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    frameworks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    testing_tools: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    databases: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cloud_technologies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    soft_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Structured Sections (JSON format strings)
    experience_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Array of Work Experiences
    projects_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)    # Array of Projects
    certifications_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Array of Certifications

    # Professional Links
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    other_links_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Preference Toggles
    email_notifications_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    job_alerts_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)

    completeness_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
