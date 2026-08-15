from typing import Optional
from fastapi import Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.organization import Organization, OrganizationMembership
from app.core.exceptions import UnauthorizedTenantAccessException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

class TenantContext:
    def __init__(self, user: User, organization: Organization, role: str):
        self.user = user
        self.organization = organization
        self.role = role

def get_auth_token(
    request: Request,
    token_param: Optional[str] = Query(None, alias="token"),
    header_token: Optional[str] = Depends(oauth2_scheme)
) -> str:
    if header_token:
        return header_token
    if token_param:
        return token_param
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_user(
    token: str = Depends(get_auth_token),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: Optional[str] = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user

def get_current_tenant(
    token: str = Depends(get_auth_token),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TenantContext:
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedTenantAccessException()

    org_id = payload.get("org_id")
    if not org_id:
        raise UnauthorizedTenantAccessException()

    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == user.id
        )
        .first()
    )

    if not membership:
        raise UnauthorizedTenantAccessException()

    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise UnauthorizedTenantAccessException()

    return TenantContext(user=user, organization=organization, role=membership.role.value)
