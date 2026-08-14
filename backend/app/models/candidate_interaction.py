from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, Integer, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin, utc_now

class CandidateInteraction(Base, TimestampMixin):
    __tablename__ = "candidate_interactions"
    __table_args__ = (
        Index("ix_candidate_interactions_cand", "candidate_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    contact_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hr_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    interaction_type: Mapped[str] = mapped_column(String(50), default="CALL", nullable=False)  # CALL, EMAIL, LINKEDIN, MESSAGE, INTERVIEW
    outcome: Mapped[str] = mapped_column(String(100), default="CONNECTED", nullable=False)     # RESUME_REQUESTED, INTERVIEW_SCHEDULED, REQUIREMENT_CLOSED, CONNECTED, NO_ANSWER
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    
    next_move: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    interaction_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
