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

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
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
    org_id: Optional[int] = None
    role: Optional[str] = None

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
