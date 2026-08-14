import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Enum, ForeignKey, Integer, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, utc_now

if TYPE_CHECKING:
    from app.models.company import Contact
    from app.models.candidate import Candidate
    from app.models.user import User

class CallType(str, enum.Enum):
    OUTBOUND = "OUTBOUND"
    INBOUND = "INBOUND"
    DISCOVERY = "DISCOVERY"
    FOLLOWUP = "FOLLOWUP"

class CallOutcome(str, enum.Enum):
    CONNECTED = "CONNECTED"
    NO_ANSWER = "NO_ANSWER"
    BUSY = "BUSY"
    CALL_BACK = "CALL_BACK"
    WRONG_NUMBER = "WRONG_NUMBER"
    NOT_HIRING = "NOT_HIRING"
    OPPORTUNITY_AVAILABLE = "OPPORTUNITY_AVAILABLE"
    RESUME_REQUESTED = "RESUME_REQUESTED"
    REQUIREMENT_CLOSED = "REQUIREMENT_CLOSED"
    NOT_RELEVANT = "NOT_RELEVANT"
    OTHER = "OTHER"

class FollowupStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class FollowupPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class EntityType(str, enum.Enum):
    COMPANY = "COMPANY"
    CONTACT = "CONTACT"
    REQUIREMENT = "REQUIREMENT"
    APPLICATION = "APPLICATION"

class Call(Base, TimestampMixin):
    __tablename__ = "calls"
    __table_args__ = (
        Index("ix_calls_org_contact", "organization_id", "contact_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    contact_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), index=True, nullable=True)
    candidate_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("candidates.id", ondelete="SET NULL"), index=True, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    call_type: Mapped[CallType] = mapped_column(Enum(CallType), default=CallType.OUTBOUND, nullable=False)
    outcome: Mapped[CallOutcome] = mapped_column(Enum(CallOutcome), default=CallOutcome.CONNECTED, nullable=False)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    called_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="calls")

class Followup(Base, TimestampMixin):
    __tablename__ = "followups"
    __table_args__ = (
        Index("ix_followups_org_due_status", "organization_id", "due_date", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    assigned_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[FollowupStatus] = mapped_column(Enum(FollowupStatus), default=FollowupStatus.PENDING, nullable=False, index=True)
    priority: Mapped[FollowupPriority] = mapped_column(Enum(FollowupPriority), default=FollowupPriority.MEDIUM, nullable=False)
    
    entity_type: Mapped[Optional[EntityType]] = mapped_column(Enum(EntityType), nullable=True)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
