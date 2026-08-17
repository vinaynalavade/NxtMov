from typing import List, Set, Union, Sequence
from fastapi import Depends, HTTPException, status
from app.models.organization import OrgRole
from app.core.tenant import TenantContext, get_current_tenant

# ==============================================================================
# CANONICAL PERMISSIONS DEFINITION
# ==============================================================================

class Permission:
    # Workspace & Members
    ORG_MANAGE = "org.manage"
    ORGANIZATION_SETTINGS = "org.manage"
    USERS_VIEW = "users.view"
    USERS_MANAGE = "users.manage"
    ROLES_MANAGE = "roles.manage"
    
    # Students & Mentorship
    STUDENTS_VIEW_ALL = "students.view_all"
    STUDENTS_VIEW_ASSIGNED = "students.view_assigned"
    STUDENTS_MANAGE = "students.manage"
    MENTORSHIP_VIEW = "mentorship.view"
    MENTORSHIP_MANAGE = "mentorship.manage"
    
    # Recruitment & Candidates
    CANDIDATES_VIEW = "candidates.view"
    CANDIDATES_MANAGE = "candidates.manage"
    CANDIDATES_ASSIGN = "candidates.assign"
    
    # Jobs & Opportunities
    JOBS_VIEW = "jobs.view"
    JOBS_MANAGE = "jobs.manage"
    
    # Applications
    APPLICATIONS_VIEW_ALL = "applications.view_all"
    APPLICATIONS_MANAGE = "applications.manage"
    APPLICATIONS_OWN_VIEW = "applications.own.view"
    APPLICATIONS_OWN_CREATE = "applications.own.create"
    
    # Submissions & Clients
    SUBMISSIONS_VIEW = "submissions.view"
    SUBMISSIONS_MANAGE = "submissions.manage"
    COMPANIES_VIEW = "companies.view"
    COMPANIES_MANAGE = "companies.manage"
    CONTACTS_VIEW = "contacts.view"
    CONTACTS_MANAGE = "contacts.manage"
    
    # Activity & CRM
    ACTIVITY_VIEW = "activity.view"
    ACTIVITY_MANAGE = "activity.manage"
    
    # Talent Profile & Resume
    PROFILE_OWN = "profile.own"
    RESUME_OWN = "resume.own"
    RECOMMENDATIONS_VIEW = "recommendations.view"
    
    # Analytics & Reports
    ANALYTICS_WORKSPACE = "analytics.workspace"

# ==============================================================================
# ROLE -> PERMISSION MAPPING MATRIX
# ==============================================================================

ADMIN_PERMISSIONS: Set[str] = {
    Permission.ORG_MANAGE,
    Permission.USERS_VIEW,
    Permission.USERS_MANAGE,
    Permission.ROLES_MANAGE,
    Permission.STUDENTS_VIEW_ALL,
    Permission.STUDENTS_VIEW_ASSIGNED,
    Permission.STUDENTS_MANAGE,
    Permission.MENTORSHIP_VIEW,
    Permission.MENTORSHIP_MANAGE,
    Permission.CANDIDATES_VIEW,
    Permission.CANDIDATES_MANAGE,
    Permission.CANDIDATES_ASSIGN,
    Permission.JOBS_VIEW,
    Permission.JOBS_MANAGE,
    Permission.APPLICATIONS_VIEW_ALL,
    Permission.APPLICATIONS_MANAGE,
    Permission.APPLICATIONS_OWN_VIEW,
    Permission.APPLICATIONS_OWN_CREATE,
    Permission.SUBMISSIONS_VIEW,
    Permission.SUBMISSIONS_MANAGE,
    Permission.COMPANIES_VIEW,
    Permission.COMPANIES_MANAGE,
    Permission.CONTACTS_VIEW,
    Permission.CONTACTS_MANAGE,
    Permission.ACTIVITY_VIEW,
    Permission.ACTIVITY_MANAGE,
    Permission.PROFILE_OWN,
    Permission.RESUME_OWN,
    Permission.RECOMMENDATIONS_VIEW,
    Permission.ANALYTICS_WORKSPACE,
}

MENTOR_PERMISSIONS: Set[str] = {
    Permission.STUDENTS_VIEW_ASSIGNED,
    Permission.MENTORSHIP_VIEW,
    Permission.MENTORSHIP_MANAGE,
    Permission.JOBS_VIEW,
    Permission.APPLICATIONS_OWN_VIEW,
    Permission.ACTIVITY_VIEW,
    Permission.PROFILE_OWN,
    Permission.RESUME_OWN,
    Permission.RECOMMENDATIONS_VIEW,
}

RECRUITER_PERMISSIONS: Set[str] = {
    Permission.USERS_VIEW,
    Permission.STUDENTS_VIEW_ALL,
    Permission.STUDENTS_VIEW_ASSIGNED,
    Permission.CANDIDATES_VIEW,
    Permission.CANDIDATES_MANAGE,
    Permission.CANDIDATES_ASSIGN,
    Permission.JOBS_VIEW,
    Permission.JOBS_MANAGE,
    Permission.APPLICATIONS_VIEW_ALL,
    Permission.APPLICATIONS_MANAGE,
    Permission.APPLICATIONS_OWN_VIEW,
    Permission.SUBMISSIONS_VIEW,
    Permission.SUBMISSIONS_MANAGE,
    Permission.COMPANIES_VIEW,
    Permission.COMPANIES_MANAGE,
    Permission.CONTACTS_VIEW,
    Permission.CONTACTS_MANAGE,
    Permission.ACTIVITY_VIEW,
    Permission.ACTIVITY_MANAGE,
    Permission.PROFILE_OWN,
    Permission.RESUME_OWN,
    Permission.RECOMMENDATIONS_VIEW,
    Permission.ANALYTICS_WORKSPACE,
}

STUDENT_PERMISSIONS: Set[str] = {
    Permission.JOBS_VIEW,
    Permission.APPLICATIONS_OWN_VIEW,
    Permission.APPLICATIONS_OWN_CREATE,
    Permission.ACTIVITY_VIEW,
    Permission.PROFILE_OWN,
    Permission.RESUME_OWN,
    Permission.RECOMMENDATIONS_VIEW,
    Permission.MENTORSHIP_VIEW,
}

COUNSELOR_PERMISSIONS: Set[str] = {
    Permission.USERS_VIEW,
    Permission.STUDENTS_VIEW_ALL,
    Permission.STUDENTS_VIEW_ASSIGNED,
    Permission.STUDENTS_MANAGE,
    Permission.MENTORSHIP_VIEW,
    Permission.MENTORSHIP_MANAGE,
    Permission.CANDIDATES_VIEW,
    Permission.CANDIDATES_MANAGE,
    Permission.CANDIDATES_ASSIGN,
    Permission.JOBS_VIEW,
    Permission.APPLICATIONS_OWN_VIEW,
    Permission.COMPANIES_VIEW,
    Permission.CONTACTS_VIEW,
    Permission.ACTIVITY_VIEW,
    Permission.ACTIVITY_MANAGE,
    Permission.PROFILE_OWN,
    Permission.RESUME_OWN,
    Permission.RECOMMENDATIONS_VIEW,
}

ROLE_PERMISSIONS_MAP = {
    OrgRole.ADMIN: ADMIN_PERMISSIONS,
    OrgRole.MENTOR: MENTOR_PERMISSIONS,
    OrgRole.RECRUITER: RECRUITER_PERMISSIONS,
    OrgRole.STUDENT: STUDENT_PERMISSIONS,
    OrgRole.COUNSELOR: COUNSELOR_PERMISSIONS,
    OrgRole.CANDIDATE: STUDENT_PERMISSIONS,  # Backward compatibility alias
}

def normalize_role(role_val: Union[OrgRole, str]) -> OrgRole:
    if isinstance(role_val, OrgRole):
        return role_val
    try:
        return OrgRole(role_val.upper())
    except (ValueError, AttributeError):
        return OrgRole.STUDENT

def get_role_permissions(role_val: Union[OrgRole, str]) -> List[str]:
    norm_role = normalize_role(role_val)
    perms = ROLE_PERMISSIONS_MAP.get(norm_role, STUDENT_PERMISSIONS)
    return sorted(list(perms))

def has_permission(role_val: Union[OrgRole, str], permission: str, is_superuser: bool = False) -> bool:
    if is_superuser:
        return True
    norm_role = normalize_role(role_val)
    perms = ROLE_PERMISSIONS_MAP.get(norm_role, set())
    return permission in perms

# ==============================================================================
# FASTAPI DEPENDENCY FACTORIES
# ==============================================================================

def require_role(*allowed_roles: Union[OrgRole, str]):
    """
    Dependency ensuring the authenticated user has one of the specified organization roles
    or is a global superuser.
    """
    normalized_allowed = {
        r.value if isinstance(r, OrgRole) else str(r).upper()
        for r in allowed_roles
    }
    # If STUDENT is allowed, also accept legacy CANDIDATE alias
    if "STUDENT" in normalized_allowed:
        normalized_allowed.add("CANDIDATE")

    def role_checker(ctx: TenantContext = Depends(get_current_tenant)) -> TenantContext:
        if ctx.user.is_superuser:
            return ctx
        
        current_role_str = ctx.role.value if hasattr(ctx.role, "value") else str(ctx.role).upper()
        if current_role_str not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: This operation requires one of the following roles: {', '.join(sorted(normalized_allowed))}."
            )
        return ctx

    return role_checker

def require_permission(permission: str):
    """
    Dependency ensuring the authenticated user has the specified fine-grained permission.
    """
    def permission_checker(ctx: TenantContext = Depends(get_current_tenant)) -> TenantContext:
        if ctx.user.is_superuser:
            return ctx
        
        current_role = normalize_role(ctx.role)
        perms = ROLE_PERMISSIONS_MAP.get(current_role, set())
        if permission not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: You lack the required permission '{permission}' for this workspace."
            )
        return ctx

    return permission_checker

def require_any_permission(*permissions: str):
    """
    Dependency ensuring the authenticated user has at least one of the specified permissions.
    """
    def any_permission_checker(ctx: TenantContext = Depends(get_current_tenant)) -> TenantContext:
        if ctx.user.is_superuser:
            return ctx

        current_role = normalize_role(ctx.role)
        perms = ROLE_PERMISSIONS_MAP.get(current_role, set())
        if not any(p in perms for p in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Insufficient permissions for this workspace operation."
            )
        return ctx

    return any_permission_checker
