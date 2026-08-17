// ==============================================================================
// NxtMov Authoritative Account Types & Permissions Matrix (Frontend)
// ==============================================================================

export const ROLES = {
  ADMIN: "ADMIN",
  MENTOR: "MENTOR",
  STUDENT: "STUDENT",
  RECRUITER: "RECRUITER"
};

export const ROLE_CONFIG = {
  ADMIN: {
    name: "ADMIN",
    title: "Administrator",
    badgeClass: "badge-admin",
    icon: "shield-check",
    description: "Platform oversight, mentor approvals, user governance, and system operations."
  },
  MENTOR: {
    name: "MENTOR",
    title: "Mentor",
    badgeClass: "badge-mentor",
    icon: "user-check",
    description: "Student progress monitoring, guidance sessions, ATS readiness, and feedback."
  },
  STUDENT: {
    name: "STUDENT",
    title: "Student",
    badgeClass: "badge-student",
    icon: "graduation-cap",
    description: "Personal resume intelligence, opportunity matching, and application tracking."
  },
  RECRUITER: {
    name: "RECRUITER",
    title: "Recruiter",
    badgeClass: "badge-recruiter",
    icon: "briefcase",
    description: "Candidate sourcing, client mandates, submissions, and placements."
  }
};

// Route access control matrix by Canonical Account Type
export const ROUTE_PERMISSIONS = {
  "dashboard": ["ADMIN", "MENTOR", "STUDENT", "RECRUITER"],
  "profile": ["ADMIN", "MENTOR", "STUDENT", "RECRUITER"],
  "resume": ["STUDENT", "ADMIN", "MENTOR"],
  "resumes": ["STUDENT", "ADMIN", "MENTOR"],
  "recommendations": ["STUDENT", "ADMIN", "MENTOR"],
  "applications": ["ADMIN", "MENTOR", "STUDENT", "RECRUITER"],
  "opportunities": ["ADMIN", "MENTOR", "STUDENT", "RECRUITER"],
  "mentor": ["MENTOR", "ADMIN"],
  "admin": ["ADMIN"],
  "admin-applications": ["ADMIN"],
  "admin-students": ["ADMIN"],
  "admin-mentors": ["ADMIN"],
  "admin-users": ["ADMIN"],
  "candidates": ["ADMIN", "RECRUITER"],
  "companies": ["ADMIN", "RECRUITER"],
  "contacts": ["ADMIN", "RECRUITER"],
  "followups": ["ADMIN", "MENTOR", "STUDENT", "RECRUITER"],
  "submissions": ["ADMIN", "RECRUITER"],
  "import": ["ADMIN", "RECRUITER"],
  "team": ["ADMIN"]
};

/**
 * Gets the current authoritative account type from store (Backend Source of Truth)
 */
export function getCurrentUserRole(store) {
  if (!store || !store.state) return ROLES.STUDENT;

  // 1. Direct Backend Source of Truth: user.account_type
  if (store.state.user?.account_type) {
    const act = String(store.state.user.account_type).toUpperCase();
    if (act === "CANDIDATE") return ROLES.STUDENT;
    if (act in ROLES) return act;
  }

  // 2. Token payload fallback
  const token = store.state.token || (typeof localStorage !== "undefined" && localStorage.getItem("nxtmov_token"));
  if (token) {
    try {
      const parts = token.split(".");
      if (parts.length === 3) {
        const payload = JSON.parse(atob(parts[1]));
        if (payload.account_type) {
          const act = String(payload.account_type).toUpperCase();
          if (act === "CANDIDATE") return ROLES.STUDENT;
          if (act in ROLES) return act;
        }
        if (payload.role) {
          const r = String(payload.role).toUpperCase();
          if (r === "CANDIDATE") return ROLES.STUDENT;
          if (r in ROLES) return r;
        }
      }
    } catch (e) {
      // ignore
    }
  }

  return ROLES.STUDENT;
}

/**
 * Verifies if a given role / account type is allowed to access a route
 */
export function isRouteAllowed(routeKey, role) {
  if (!routeKey) return true;
  const cleanRoute = routeKey.replace(/^#\/?/, "").split("/")[0].split("?")[0];
  if (!cleanRoute || cleanRoute === "") return true;

  const allowedRoles = ROUTE_PERMISSIONS[cleanRoute];
  if (!allowedRoles) {
    return true;
  }

  const userRole = (role || ROLES.STUDENT).toUpperCase();
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
