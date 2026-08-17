// ==============================================================================
// NxtMov Canonical RBAC & Permissions Matrix (Frontend)
// ==============================================================================

export const ROLES = {
  ADMIN: "ADMIN",
  MENTOR: "MENTOR",
  RECRUITER: "RECRUITER",
  STUDENT: "STUDENT",
  COUNSELOR: "COUNSELOR"
};

export const ROLE_CONFIG = {
  ADMIN: {
    name: "ADMIN",
    title: "Workspace Administrator",
    badgeClass: "badge-admin",
    icon: "shield-check",
    description: "Full workspace configuration, team management, and operations control."
  },
  MENTOR: {
    name: "MENTOR",
    title: "Student Mentor",
    badgeClass: "badge-mentor",
    icon: "user-check",
    description: "Guiding assigned students, reviewing ATS readiness, and interview prep."
  },
  RECRUITER: {
    name: "RECRUITER",
    title: "Talent Partner / Recruiter",
    badgeClass: "badge-recruiter",
    icon: "briefcase",
    description: "Candidate sourcing, employer client CRM, submissions, and placements."
  },
  STUDENT: {
    name: "STUDENT",
    title: "Student / Talent",
    badgeClass: "badge-student",
    icon: "graduation-cap",
    description: "Personal resume intelligence, opportunity matching, and application tracking."
  },
  COUNSELOR: {
    name: "COUNSELOR",
    title: "Career Counselor",
    badgeClass: "badge-counselor",
    icon: "compass",
    description: "Career advisory, student assessment, and placement guidance."
  }
};

// Route access control matrix by Canonical Role
export const ROUTE_PERMISSIONS = {
  "dashboard": ["ADMIN", "MENTOR", "RECRUITER", "STUDENT", "COUNSELOR"],
  "mentor-dashboard": ["ADMIN", "MENTOR", "COUNSELOR", "RECRUITER"],
  "student-dashboard": ["STUDENT", "ADMIN"],
  "profile": ["ADMIN", "MENTOR", "RECRUITER", "STUDENT", "COUNSELOR"],
  "resumes": ["STUDENT", "ADMIN", "MENTOR", "COUNSELOR"],
  "recommendations": ["STUDENT", "ADMIN", "MENTOR", "COUNSELOR"],
  "applications": ["ADMIN", "MENTOR", "RECRUITER", "STUDENT", "COUNSELOR"],
  "opportunities": ["ADMIN", "MENTOR", "RECRUITER", "STUDENT", "COUNSELOR"],
  "candidates": ["ADMIN", "RECRUITER", "COUNSELOR"],
  "companies": ["ADMIN", "RECRUITER", "COUNSELOR"],
  "contacts": ["ADMIN", "RECRUITER", "COUNSELOR"],
  "activity": ["ADMIN", "RECRUITER", "COUNSELOR"],
  "submissions": ["ADMIN", "RECRUITER"],
  "placements": ["ADMIN", "RECRUITER"],
  "import": ["ADMIN", "RECRUITER"],
  "team": ["ADMIN"],
  "workspace-settings": ["ADMIN"]
};

/**
 * Gets the current active role string from store / token
 */
export function getCurrentUserRole(store) {
  if (!store || !store.state) return ROLES.STUDENT;
  
  // 1. Check user.active_organization.role
  if (store.state.user?.active_organization?.role) {
    const r = String(store.state.user.active_organization.role).toUpperCase();
    return r === "CANDIDATE" ? ROLES.STUDENT : r;
  }

  // 2. Check token payload if stored in state or localStorage
  const token = store.state.token || (typeof localStorage !== "undefined" && localStorage.getItem("nxtmov_token"));
  if (token) {
    try {
      const parts = token.split(".");
      if (parts.length === 3) {
        const payload = JSON.parse(atob(parts[1]));
        if (payload.role) {
          const r = String(payload.role).toUpperCase();
          return r === "CANDIDATE" ? ROLES.STUDENT : r;
        }
      }
    } catch (e) {
      // fallback
    }
  }

  // 3. Check user roles array for activeOrgId match
  if (store.state.user?.roles && store.state.user.roles.length > 0) {
    const activeOrgId = store.state.activeOrgId || store.state.user?.active_organization?.id;
    if (activeOrgId) {
      const match = store.state.user.roles.find(r => r.organization_id === activeOrgId);
      if (match && match.role) {
        const r = String(match.role).toUpperCase();
        return r === "CANDIDATE" ? ROLES.STUDENT : r;
      }
    }
  }

  return ROLES.STUDENT;
}

/**
 * Verifies if a given role is allowed to access a route
 */
export function isRouteAllowed(routeKey, role) {
  if (!routeKey) return true;
  const cleanRoute = routeKey.replace(/^#\/?/, "").split("/")[0].split("?")[0];
  if (!cleanRoute || cleanRoute === "") return true;

  const allowedRoles = ROUTE_PERMISSIONS[cleanRoute];
  if (!allowedRoles) {
    // Default open for unrecognized public/common routes
    return true;
  }

  const userRole = (role || ROLES.STUDENT).toUpperCase();
  // Map legacy CANDIDATE to STUDENT
  const normalizedRole = userRole === "CANDIDATE" ? ROLES.STUDENT : userRole;

  return allowedRoles.includes(normalizedRole);
}

/**
 * Verifies if the current user has a specific fine-grained permission
 */
export function hasPermission(store, permissionName) {
  if (!store || !store.state || !store.state.user) return false;
  if (store.state.user.is_superuser) return true;
  
  const perms = store.state.user.permissions || [];
  return perms.includes(permissionName);
}
