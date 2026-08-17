from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict

class ActiveOrgInfo(BaseModel):
    id: int
    name: str
    role: str

    model_config = ConfigDict(from_attributes=True)

class UserRoleInfo(BaseModel):
    organization_id: int
    role: str
    organization_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: str
    full_name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    password: str
    account_type: Optional[str] = "STUDENT"

class StudentRegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    phone: Optional[str] = None

class MentorApplicationCreate(BaseModel):
    full_name: str
    official_email: str
    institute_name: str
    employee_id: str
    department: Optional[str] = None
    designation: Optional[str] = None
    password: str
    phone: Optional[str] = None

class MentorApplicationResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    full_name: str
    official_email: str
    institute_name: str
    employee_id: str
    department: Optional[str] = None
    designation: Optional[str] = None
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    rejection_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class MentorApprovalAction(BaseModel):
    rejection_reason: Optional[str] = None

class AdminBootstrapRequest(BaseModel):
    bootstrap_key: str
    full_name: str
    email: str
    password: str

class AdminInviteRequest(BaseModel):
    email: str
    full_name: Optional[str] = None
    account_type: str = "ADMIN"  # "ADMIN" or "MENTOR"

class UserStatusUpdate(BaseModel):
    status: str
    is_active: Optional[bool] = None

class UserLogin(BaseModel):
    email: str
    password: str
    requested_account_type: Optional[str] = None

class UserResponse(UserBase):
    id: int
    account_type: str = "STUDENT"
    status: str = "ACTIVE"
    is_active: bool = True
    is_superuser: bool = False
    is_email_verified: bool = False
    is_phone_verified: bool = False
    headline: Optional[str] = None
    location: Optional[str] = None
    active_organization: Optional[ActiveOrgInfo] = None
    roles: List[UserRoleInfo] = []
    permissions: List[str] = []

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    active_org_id: int
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)

class TokenPayload(BaseModel):
    sub: Optional[int] = None
    account_type: Optional[str] = None
    status: Optional[str] = None
    role: Optional[str] = None
    org_id: Optional[int] = None

class EmailVerifyRequest(BaseModel):
    email: Optional[str] = None

class EmailVerifyConfirm(BaseModel):
    token: str

class PhoneOTPRequest(BaseModel):
    phone: str

class PhoneOTPConfirm(BaseModel):
    phone: str
    otp: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
