import enum
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization, OrganizationMembership
    from app.models.mentor_application import MentorApplication

class AccountType(str, enum.Enum):
    STUDENT = "STUDENT"
    MENTOR = "MENTOR"
    ADMIN = "ADMIN"
    RECRUITER = "RECRUITER"

class AccountStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    SUSPENDED = "SUSPENDED"
    REJECTED = "REJECTED"

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Canonical Account Type and Lifecycle Status
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType), default=AccountType.STUDENT, nullable=False)
    status: Mapped[AccountStatus] = mapped_column(Enum(AccountStatus), default=AccountStatus.ACTIVE, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone_otp: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    owned_organizations: Mapped[List["Organization"]] = relationship("Organization", back_populates="owner", cascade="all, delete-orphan")
    memberships: Mapped[List["OrganizationMembership"]] = relationship("OrganizationMembership", back_populates="user", cascade="all, delete-orphan")
    mentor_applications: Mapped[List["MentorApplication"]] = relationship("MentorApplication", foreign_keys="[MentorApplication.user_id]", back_populates="user", cascade="all, delete-orphan")
