import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Integer, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, utc_now

if TYPE_CHECKING:
    from app.models.user import User

class MentorApplicationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class MentorApplication(Base, TimestampMixin):
    __tablename__ = "mentor_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    official_email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    institute_name: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    designation: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    status: Mapped[MentorApplicationStatus] = mapped_column(Enum(MentorApplicationStatus), default=MentorApplicationStatus.PENDING, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id], back_populates="mentor_applications")
    reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by])
