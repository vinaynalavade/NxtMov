import enum
from datetime import date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Enum, ForeignKey, Integer, Numeric, Date, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company, Contact
    from app.models.application import Application, Submission

class EmploymentType(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    CONTRACT = "CONTRACT"
    PART_TIME = "PART_TIME"
    INTERNSHIP = "INTERNSHIP"

class WorkMode(str, enum.Enum):
    HYBRID = "HYBRID"
    REMOTE = "REMOTE"
    ONSITE = "ONSITE"

class RequirementPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class RequirementStatus(str, enum.Enum):
    OPEN = "OPEN"
    NEW = "NEW"
    INTERESTED = "INTERESTED"
    APPLIED = "APPLIED"
    FOLLOW_UP = "FOLLOW_UP"
    INTERVIEWING = "INTERVIEWING"
    OFFER = "OFFER"
    ON_HOLD = "ON_HOLD"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class JobRequirement(Base, TimestampMixin):
    __tablename__ = "job_requirements"
    __table_args__ = (
        Index("ix_requirements_org_status", "organization_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)
    contact_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    work_mode: Mapped[WorkMode] = mapped_column(Enum(WorkMode), default=WorkMode.HYBRID, nullable=False)
    priority: Mapped[RequirementPriority] = mapped_column(Enum(RequirementPriority), default=RequirementPriority.MEDIUM, nullable=False)
    
    experience_req: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    min_experience_years: Mapped[Optional[float]] = mapped_column(Numeric(4, 1), nullable=True)
    max_experience_years: Mapped[Optional[float]] = mapped_column(Numeric(4, 1), nullable=True)
    skills_req: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    employment_type: Mapped[EmploymentType] = mapped_column(Enum(EmploymentType), default=EmploymentType.FULL_TIME, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    openings_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    min_salary: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    max_salary: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[RequirementStatus] = mapped_column(Enum(RequirementStatus), default=RequirementStatus.OPEN, nullable=False)
    
    open_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    closing_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    assigned_recruiter_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="requirements")
    contact: Mapped[Optional["Contact"]] = relationship("Contact")
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="job_requirement", cascade="all, delete-orphan")
    submissions: Mapped[List["Submission"]] = relationship("Submission", back_populates="job_requirement", cascade="all, delete-orphan")
