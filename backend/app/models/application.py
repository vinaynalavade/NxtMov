import enum
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Enum, ForeignKey, Integer, DateTime, Date, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, utc_now

if TYPE_CHECKING:
    from app.models.requirement import JobRequirement
    from app.models.candidate import Candidate

class ApplicationStage(str, enum.Enum):
    APPLIED = "APPLIED"
    SUBMITTED = "SUBMITTED"
    SCREENING = "SCREENING"
    INTERVIEWING = "INTERVIEWING"
    OFFERED = "OFFERED"
    PLACED = "PLACED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"

class SubmissionStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    SHORTLISTED = "SHORTLISTED"
    CLIENT_REVIEW = "CLIENT_REVIEW"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    PLACED = "PLACED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"

class InterviewOutcome(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    PASSED = "PASSED"
    FAILED = "FAILED"
    RESCHEDULED = "RESCHEDULED"
    CANCELLED = "CANCELLED"

class OfferStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    REVISED = "REVISED"

class PlacementStatus(str, enum.Enum):
    EXPECTED = "EXPECTED"
    CONFIRMED = "CONFIRMED"
    JOINED = "JOINED"
    DID_NOT_JOIN = "DID_NOT_JOIN"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    EARLY_EXIT = "EARLY_EXIT"
    CANCELLED = "CANCELLED"

class Submission(Base, TimestampMixin):
    __tablename__ = "submissions"
    __table_args__ = (
        Index("ix_submissions_org_req_cand", "organization_id", "job_requirement_id", "candidate_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    job_requirement_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_requirements.id", ondelete="CASCADE"), index=True, nullable=False)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False)
    submitted_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus), default=SubmissionStatus.SUBMITTED, nullable=False)
    client_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    job_requirement: Mapped["JobRequirement"] = relationship("JobRequirement", back_populates="submissions")
    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="submissions")

class Application(Base, TimestampMixin):
    __tablename__ = "applications"
    __table_args__ = (
        Index("ix_applications_org_req_cand", "organization_id", "job_requirement_id", "candidate_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    job_requirement_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_requirements.id", ondelete="CASCADE"), index=True, nullable=False)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False)

    stage: Mapped[ApplicationStage] = mapped_column(Enum(ApplicationStage), default=ApplicationStage.APPLIED, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    job_requirement: Mapped["JobRequirement"] = relationship("JobRequirement", back_populates="applications")
    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="applications")
    interviews: Mapped[List["Interview"]] = relationship("Interview", back_populates="application", cascade="all, delete-orphan")
    offer: Mapped[Optional["Offer"]] = relationship("Offer", back_populates="application", uselist=False, cascade="all, delete-orphan")
    placement: Mapped[Optional["Placement"]] = relationship("Placement", back_populates="application", uselist=False, cascade="all, delete-orphan")

class Interview(Base, TimestampMixin):
    __tablename__ = "interviews"
    __table_args__ = (
        Index("ix_interviews_app_scheduled", "application_id", "scheduled_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False)

    round_name: Mapped[str] = mapped_column(String(150), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location_or_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    interviewer_names: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    outcome: Mapped[InterviewOutcome] = mapped_column(Enum(InterviewOutcome), default=InterviewOutcome.SCHEDULED, nullable=False)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="interviews")

class Offer(Base, TimestampMixin):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)

    offered_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    joining_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[OfferStatus] = mapped_column(Enum(OfferStatus), default=OfferStatus.PENDING, nullable=False)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="offer")

class Placement(Base, TimestampMixin):
    __tablename__ = "placements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    application_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("applications.id", ondelete="SET NULL"), unique=True, index=True, nullable=True)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False)
    job_requirement_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_requirements.id", ondelete="CASCADE"), index=True, nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)

    join_date: Mapped[date] = mapped_column(Date, nullable=False)
    offered_salary: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    billing_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    recruiter_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    counselor_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[PlacementStatus] = mapped_column(Enum(PlacementStatus), default=PlacementStatus.CONFIRMED, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    application: Mapped[Optional["Application"]] = relationship("Application", back_populates="placement")
