import { api } from "./api.js";
import { store } from "./store.js";
import { updateSidebarActiveRoute } from "./sidebar.js";
import {
  renderLogin, initLoginListeners,
  renderRegister, initRegisterListeners,
  renderApplyMentor, initApplyMentorListeners,
  renderAdminBootstrap, initAdminBootstrapListeners,
  renderVerifyEmail, initVerifyEmailListeners
} from "./views/auth.js";
import { renderDashboard, initDashboardListeners } from "./views/dashboard.js";
import { renderAdminView, initAdminListeners } from "./views/admin.js";
import { renderCompanies, initCompaniesListeners } from "./views/companies.js";
import { renderContacts, initContactsListeners } from "./views/contacts.js";
import { renderFollowups, initFollowupsListeners } from "./views/followups.js";
import { renderImport, initImportListeners } from "./views/import.js";
import { renderOpportunities, initOpportunitiesListeners } from "./views/opportunities.js";
import { renderApplications, initApplicationsListeners } from "./views/applications.js";
import { renderCandidatesView } from "./views/candidates.js";
import { renderSubmissionsView } from "./views/submissions.js";
import { renderTeamView } from "./views/team.js";
import { renderProfile, initProfileListeners } from "./views/profile.js";
import { renderResume, initResumeListeners } from "./views/resume.js";
import { renderRecommendations, initRecommendationsListeners } from "./views/recommendations.js";
import { renderMentorView, initMentorListeners } from "./views/mentor.js";
import { initPasswordToggle } from "./components.js";

import { getCurrentUserRole, isRouteAllowed, ROLE_CONFIG } from "./permissions.js";

const routes = {
  "/login": { render: renderLogin, init: initLoginListeners, public: true },
  "/register": { render: renderRegister, init: initRegisterListeners, public: true },
  "/apply-mentor": { render: renderApplyMentor, init: initApplyMentorListeners, public: true },
  "/admin-bootstrap": { render: renderAdminBootstrap, init: initAdminBootstrapListeners, public: true },
  "/verify-email": { render: renderVerifyEmail, init: initVerifyEmailListeners, public: true },
  "/dashboard": { render: renderDashboard, init: initDashboardListeners },
  "/admin": { render: renderAdminView, init: initAdminListeners },
  "/admin-applications": { render: renderAdminView, init: initAdminListeners },
  "/admin-students": { render: renderAdminView, init: initAdminListeners },
  "/admin-mentors": { render: renderAdminView, init: initAdminListeners },
  "/admin-users": { render: renderAdminView, init: initAdminListeners },
  "/profile": { render: renderProfile, init: initProfileListeners },
  "/resume": { render: renderResume, init: initResumeListeners },
  "/recommendations": { render: renderRecommendations, init: initRecommendationsListeners },
  "/mentor": { render: renderMentorView, init: initMentorListeners },
  "/companies": { render: renderCompanies, init: initCompaniesListeners },
  "/contacts": { render: renderContacts, init: initContactsListeners },
  "/followups": { render: renderFollowups, init: initFollowupsListeners },
  "/import": { render: renderImport, init: initImportListeners },
  "/opportunities": { render: renderOpportunities, init: initOpportunitiesListeners },
  "/applications": { render: renderApplications, init: initApplicationsListeners },
  "/candidates": { render: (container) => renderCandidatesView(container), isDynamic: true },
  "/submissions": { render: (container) => renderSubmissionsView(container), isDynamic: true },
  "/team": { render: (container) => renderTeamView(container), isDynamic: true },
};

export class Router {
  static init() {
    window.addEventListener("hashchange", () => this.handleRoute());
    this.handleRoute();
  }

  static renderAccessRestricted(container, hash, userRole) {
    const roleMeta = ROLE_CONFIG[userRole] || ROLE_CONFIG.STUDENT;
    const state = store.getState();
    const activeOrgName = state.user?.active_organization?.name || "Current Workspace";

    container.innerHTML = `
      <div class="card access-restricted-card" style="max-width: 580px; margin: 3.5rem auto; text-align: center; padding: 2.5rem 2rem; border-top: 4px solid var(--accent-primary);">
        <div style="width: 56px; height: 56px; border-radius: 50%; background: rgba(239, 68, 68, 0.1); color: #ef4444; display: flex; align-items: center; justify-content: center; margin: 0 auto 1.25rem auto;">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
          </svg>
        </div>
        <h2 style="font-size: 1.5rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.5rem;">Access Restricted</h2>
        <p style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.5; margin-bottom: 1.5rem;">
          Your current active role (<strong class="role-badge ${roleMeta.badgeClass}">${roleMeta.title}</strong>) in <strong>${activeOrgName}</strong> does not have permission to view the <code>${hash}</code> page.
        </p>
        <div style="background: var(--bg-secondary); border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem; text-align: left; font-size: 0.85rem; color: var(--text-muted);">
          <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.25rem;">Role Capabilities:</div>
          ${roleMeta.description}
        </div>
        <div style="display: flex; justify-content: center; gap: 0.75rem; flex-wrap: wrap;">
          <button onclick="window.location.hash='#/dashboard'" class="btn btn-primary">
            Return to Dashboard
          </button>
        </div>
      </div>
    `;
  }

  static handleRoute() {
    let hash = window.location.hash.slice(1) || "/dashboard";
    if (hash.includes("?")) {
      hash = hash.split("?")[0];
    }

    const token = api.getToken();
    let route = routes[hash] || routes["/dashboard"];

    // Route guard for authenticated pages
    if (!route.public && !token) {
      if (window.location.hash !== "#/login") {
        window.location.hash = "#/login";
        return;
      }
      hash = "/login";
      route = routes["/login"];
    }

    // If logged in and on public page, redirect to dashboard
    if (route.public && token) {
      if (window.location.hash !== "#/dashboard") {
        window.location.hash = "#/dashboard";
        return;
      }
      hash = "/dashboard";
      route = routes["/dashboard"];
    }

    const mainContent = document.getElementById("main-content");
    if (mainContent) {
      const userRole = getCurrentUserRole(store);

      // Check role permissions for the target route
      if (!route.public && !isRouteAllowed(hash, userRole)) {
        this.renderAccessRestricted(mainContent, hash, userRole);
        this.updateActiveNav(hash);
        return;
      }

      try {
        if (route.isDynamic) {
          route.render(mainContent);
        } else {
          mainContent.innerHTML = route.render();
          if (route.init) {
            try {
              route.init();
            } catch (initErr) {
              console.warn(`View init warning for ${hash}:`, initErr);
            }
          }
        }
        initPasswordToggle(mainContent);
      } catch (err) {
        console.error(`Error rendering route ${hash}:`, err);
        mainContent.innerHTML = `
          <div class="card" style="max-width: 520px; margin: 3rem auto; text-align: center; padding: 2rem; border-left: 4px solid var(--warning-color);">
            <h3 style="color: var(--danger-color); margin-bottom: 0.5rem; font-weight: 700;">Unable to load this page</h3>
            <p style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 1.25rem;">
              ${err.message || 'An error occurred while rendering this view.'}
            </p>
            <div style="display: flex; justify-content: center; gap: 0.75rem;">
              <button onclick="window.location.hash='#/dashboard'" class="btn btn-outline">Dashboard</button>
              <button onclick="window.location.reload()" class="btn btn-primary">Retry</button>
            </div>
          </div>
        `;
      }
    }

    // Update active nav highlighting — does NOT re-render sidebar nav
    this.updateActiveNav(hash);
  }

  static updateActiveNav(currentPath) {
    // Only update active link highlighting and breadcrumb
    updateSidebarActiveRoute(currentPath);

    // Toggle workspace bar visibility based on auth
    const token = api.getToken();
    const userBar = document.getElementById("user-profile-bar");
    if (userBar) userBar.style.display = token ? "flex" : "none";

    // NOTE: We intentionally do NOT call renderSidebarNav() here.
    // The sidebar is rendered once on init and re-rendered only on store state changes.
    // Calling it on every route change caused double-render and layout flicker.
  }
}
