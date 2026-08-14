from typing import Optional
from sqlalchemy import Text, ForeignKey, Integer, Float, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin

class JobRecommendation(Base, TimestampMixin):
    __tablename__ = "job_recommendations"
    __table_args__ = (
        Index("ix_job_rec_cand_req", "candidate_id", "job_requirement_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False)
    job_requirement_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_requirements.id", ondelete="CASCADE"), index=True, nullable=False)

    match_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    score_breakdown_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_saved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
