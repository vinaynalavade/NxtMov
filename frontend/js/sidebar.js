import { store } from "./store.js";
import { api } from "./api.js";

/* ================================================================
   Navigation Schema — Single source of truth for all sidebar links
   ================================================================ */
const NAVIGATION_SCHEMA = [
  {
    category: "WORKSPACE",
    roles: ["STUDENT", "MENTOR", "COUNSELOR", "RECRUITER", "ADMIN"],
    items: [
      { path: "/dashboard", label: "Dashboard", icon: "📊" }
    ]
  },
  {
    category: "TALENT ECOSYSTEM",
    roles: ["STUDENT", "ADMIN"],
    items: [
      { path: "/profile", label: "My Profile", icon: "👤" },
      { path: "/resume", label: "Resumes & AI", icon: "📄" },
      { path: "/recommendations", label: "Role Matches", icon: "🎯" },
      { path: "/applications", label: "My Applications", icon: "📌" },
      { path: "/opportunities", label: "Requirements", icon: "💼" }
    ]
  },
  {
    category: "RECRUITMENT & CRM",
    roles: ["ADMIN", "RECRUITER", "COUNSELOR", "MENTOR"],
    items: [
      { path: "/candidates", label: "Candidates Roster", icon: "👥" },
      { path: "/opportunities", label: "Job Openings", icon: "💼" },
      { path: "/applications", label: "Applications Pipeline", icon: "📋" },
      { path: "/submissions", label: "Client Submissions", icon: "🚀" },
      { path: "/contacts", label: "HR Contacts", icon: "📇" },
      { path: "/followups", label: "Follow-ups", icon: "📞" }
    ]
  },
  {
    category: "MENTORSHIP & JOURNEY",
    roles: ["MENTOR", "COUNSELOR", "ADMIN"],
    items: [
      { path: "/mentor", label: "My Students", icon: "🎓" }
    ]
  },
  {
    category: "DATA & SYSTEM",
    roles: ["ADMIN", "RECRUITER"],
    items: [
      { path: "/companies", label: "Companies", icon: "🏢" },
      { path: "/import", label: "Importer", icon: "📥" },
      { path: "/team", label: "Team & Workspaces", icon: "⚙️" }
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

export function initSidebar() {
  if (sidebarInitialized) return; // Prevent duplicate initialization
  sidebarInitialized = true;

  const toggleBtn = document.getElementById("sidebar-toggle-btn");
  const mobileToggleBtn = document.getElementById("mobile-sidebar-toggle-btn");
  const backdrop = document.getElementById("sidebar-backdrop");

  // Restore collapsed state from localStorage
  const isCollapsed = localStorage.getItem("nxtmov_sidebar_collapsed") === "true";
  if (isCollapsed) {
    document.body.classList.add("sidebar-collapsed");
  }

  // Desktop sidebar collapse/expand toggle
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
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
        <a href="#${item.path}" class="sidebar-nav-link" data-path="${item.path}">
          <span class="sidebar-icon">${item.icon}</span>
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
function renderSidebarUserProfile() {
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
