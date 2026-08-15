import { store } from "./store.js";
import { api, getAuthenticatedFileUrl } from "./api.js";
import { getIcon } from "./icons.js";

/* ================================================================
   Navigation Schema — Single source of truth for all sidebar links
   ================================================================ */
const NAVIGATION_SCHEMA = [
  {
    category: "WORKSPACE",
    roles: ["STUDENT", "MENTOR", "COUNSELOR", "RECRUITER", "ADMIN"],
    items: [
      { path: "/dashboard", label: "Dashboard", icon: "dashboard" }
    ]
  },
  {
    category: "TALENT ECOSYSTEM",
    roles: ["STUDENT", "ADMIN"],
    items: [
      { path: "/profile", label: "My Profile", icon: "profile" },
      { path: "/resume", label: "Resume & ATS", icon: "resume" },
      { path: "/recommendations", label: "Role Matches", icon: "recommendations" },
      { path: "/applications", label: "My Applications", icon: "applications" },
      { path: "/opportunities", label: "Requirements", icon: "opportunities" }
    ]
  },
  {
    category: "RECRUITMENT & CRM",
    roles: ["ADMIN", "RECRUITER", "COUNSELOR", "MENTOR"],
    items: [
      { path: "/candidates", label: "Candidates Roster", icon: "candidates" },
      { path: "/opportunities", label: "Job Openings", icon: "opportunities" },
      { path: "/applications", label: "Applications Pipeline", icon: "applications" },
      { path: "/submissions", label: "Client Submissions", icon: "submissions" },
      { path: "/contacts", label: "HR Contacts", icon: "contacts" },
      { path: "/followups", label: "Follow-ups", icon: "followups" }
    ]
  },
  {
    category: "MENTORSHIP & JOURNEY",
    roles: ["MENTOR", "COUNSELOR", "ADMIN"],
    items: [
      { path: "/mentor", label: "My Students", icon: "mentor" }
    ]
  },
  {
    category: "DATA & SYSTEM",
    roles: ["ADMIN", "RECRUITER"],
    items: [
      { path: "/companies", label: "Companies", icon: "companies" },
      { path: "/import", label: "Importer", icon: "import" },
      { path: "/team", label: "Team & Workspaces", icon: "team" }
    ]
  }
];

/* ================================================================
   Role Detection
   ================================================================ */
export function getUserRole() {
  const state = store.getState();
  const user = state.user;
  const orgs = state.organizations || [];
  const activeOrgId = state.activeOrgId;

  if (!user) return "PUBLIC";

  const activeOrg = orgs.find(o => o.id === activeOrgId) || orgs[0];
  if (activeOrg && activeOrg.role) {
    const r = typeof activeOrg.role === "string" ? activeOrg.role : activeOrg.role.value;
    return r ? r.toUpperCase() : "STUDENT";
  }

  return user.role ? user.role.toUpperCase() : "STUDENT";
}

/* ================================================================
   Sidebar Initialization — ONE authoritative controller
   ================================================================ */
let sidebarInitialized = false;
let collapseTimer = null;

export function initSidebar() {
  if (sidebarInitialized) return; // Prevent duplicate initialization
  sidebarInitialized = true;

  const sidebarEl = document.getElementById("app-sidebar");
  const toggleBtn = document.getElementById("sidebar-toggle-btn");
  const mobileToggleBtn = document.getElementById("mobile-sidebar-toggle-btn");
  const backdrop = document.getElementById("sidebar-backdrop");

  // Restore collapsed state from localStorage
  const isCollapsed = localStorage.getItem("nxtmov_sidebar_collapsed") === "true";
  if (isCollapsed) {
    document.body.classList.add("sidebar-collapsed");
  }

  // Desktop smooth hover expand / collapse with debounce delay
  if (sidebarEl) {
    sidebarEl.addEventListener("mouseenter", () => {
      if (window.innerWidth > 992 && document.body.classList.contains("sidebar-collapsed")) {
        clearTimeout(collapseTimer);
        document.body.classList.add("sidebar-hover-expanded");
      }
    });

    sidebarEl.addEventListener("mouseleave", () => {
      if (window.innerWidth > 992 && document.body.classList.contains("sidebar-collapsed")) {
        clearTimeout(collapseTimer);
        collapseTimer = setTimeout(() => {
          document.body.classList.remove("sidebar-hover-expanded");
        }, 220);
      }
    });
  }

  // Desktop sidebar explicit toggle button
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      document.body.classList.remove("sidebar-hover-expanded");
      document.body.classList.toggle("sidebar-collapsed");
      const collapsedNow = document.body.classList.contains("sidebar-collapsed");
      localStorage.setItem("nxtmov_sidebar_collapsed", collapsedNow ? "true" : "false");
    });
  }

  // Mobile sidebar drawer toggle
  if (mobileToggleBtn) {
    mobileToggleBtn.addEventListener("click", () => {
      document.body.classList.toggle("sidebar-mobile-open");
    });
  }

  // Mobile backdrop click closes drawer
  if (backdrop) {
    backdrop.addEventListener("click", () => {
      document.body.classList.remove("sidebar-mobile-open");
    });
  }

  // Subscribe to store changes for reactive re-render
  store.subscribe(() => renderSidebarNav());

  // Initial render
  renderSidebarNav();
}

/* ================================================================
   Sidebar Nav Rendering
   ================================================================ */
export function renderSidebarNav() {
  const navContainer = document.getElementById("sidebar-nav");
  if (!navContainer) return;

  const role = getUserRole();
  const token = api.getToken();

  if (!token) {
    navContainer.innerHTML = "";
    document.body.classList.add("unauthenticated");
    return;
  }

  document.body.classList.remove("unauthenticated");

  let html = "";
  NAVIGATION_SCHEMA.forEach(group => {
    const isVisibleGroup = group.roles.includes(role) || role === "ADMIN";
    if (!isVisibleGroup) return;

    html += `<div class="sidebar-category-title">${group.category}</div>`;
    html += `<div class="sidebar-category-group">`;

    group.items.forEach(item => {
      html += `
        <a href="#${item.path}" class="sidebar-nav-link" data-path="${item.path}" title="${item.label}" data-tooltip="${item.label}">
          <span class="sidebar-icon">${getIcon(item.icon, "sidebar-svg-icon", 18)}</span>
          <span class="sidebar-label">${item.label}</span>
        </a>
      `;
    });

    html += `</div>`;
  });

  navContainer.innerHTML = html;

  // Close mobile drawer on nav link click
  navContainer.querySelectorAll(".sidebar-nav-link").forEach(link => {
    link.addEventListener("click", () => {
      document.body.classList.remove("sidebar-mobile-open");
    });
  });

  // Update current active link
  const currentHash = window.location.hash.slice(1) || "/dashboard";
  updateSidebarActiveRoute(currentHash.split("?")[0]);

  // Update bottom profile card
  renderSidebarUserProfile();
}

/* ================================================================
   Active Route Highlighting & Breadcrumb
   ================================================================ */
export function updateSidebarActiveRoute(currentPath) {
  const links = document.querySelectorAll(".sidebar-nav-link");
  let activeTitle = "Dashboard";

  links.forEach(link => {
    const path = link.getAttribute("data-path");
    if (path === currentPath) {
      link.classList.add("active");
      const labelEl = link.querySelector(".sidebar-label");
      if (labelEl) activeTitle = labelEl.textContent;
    } else {
      link.classList.remove("active");
    }
  });

  // Update top header breadcrumb title
  const titleEl = document.getElementById("page-breadcrumb-title");
  if (titleEl) {
    titleEl.textContent = activeTitle;
  }
}

/* ================================================================
   Bottom User Profile Card
   ================================================================ */
export function renderSidebarUserProfile() {
  const state = store.getState();
  const user = state.user;
  const role = getUserRole();

  const nameEl = document.getElementById("sidebar-user-name");
  const roleEl = document.getElementById("sidebar-user-role");
  const avatarEl = document.getElementById("sidebar-user-avatar");

  if (user) {
    if (nameEl) nameEl.textContent = user.full_name || user.email;
    if (roleEl) roleEl.textContent = role;
    if (avatarEl) {
      const avatarUrl = user.avatar_url || state.profile?.avatar_url;
      if (avatarUrl) {
        const fullAvatarUrl = getAuthenticatedFileUrl(avatarUrl);
        avatarEl.innerHTML = `<img src="${fullAvatarUrl}" alt="${user.full_name || 'User'}" class="user-avatar-img" onerror="this.onerror=null; this.parentElement.textContent='${(user.full_name || user.email).split(' ').map(n=>n[0]).join('').toUpperCase().slice(0,2)}';" />`;
      } else {
        const initials = (user.full_name || user.email)
          .split(" ")
          .map(n => n[0])
          .join("")
          .toUpperCase()
          .slice(0, 2);
        avatarEl.textContent = initials;
      }
    }
  }
}
