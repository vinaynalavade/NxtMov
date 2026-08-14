import enum
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Enum, ForeignKey, Integer, Float, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, utc_now

if TYPE_CHECKING:
    from app.models.application import Application, Submission

class CandidateStatus(str, enum.Enum):
    NEW = "NEW"
    SCREENING = "SCREENING"
    READY = "READY"
    SUBMITTED = "SUBMITTED"
    INTERVIEWING = "INTERVIEWING"
    OFFERED = "OFFERED"
    PLACED = "PLACED"
    ON_HOLD = "ON_HOLD"
    REJECTED = "REJECTED"
    INACTIVE = "INACTIVE"

class DocumentType(str, enum.Enum):
    RESUME = "RESUME"
    CERTIFICATE = "CERTIFICATE"
    ID_DOCUMENT = "ID_DOCUMENT"
    OTHER = "OTHER"

class Candidate(Base, TimestampMixin):
    __tablename__ = "candidates"
    __table_args__ = (
        Index("ix_candidates_org_email", "organization_id", "email"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Professional & Salary Details
    current_title: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    current_company: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    experience_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notice_period_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_salary: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    expected_salary: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    
    # Skills
    primary_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    secondary_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Consultancy Assignments
    assigned_counselor_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_recruiter_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resume_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[CandidateStatus] = mapped_column(Enum(CandidateStatus), default=CandidateStatus.NEW, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    submissions: Mapped[List["Submission"]] = relationship("Submission", back_populates="candidate", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="candidate", cascade="all, delete-orphan")

class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False)

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    doc_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), default=DocumentType.RESUME, nullable=False)

    # Relationships
    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="documents")
