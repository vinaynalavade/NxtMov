import { api } from "./api.js";
import { store } from "./store.js";
import { updateSidebarActiveRoute } from "./sidebar.js";
import { renderLogin, initLoginListeners, renderRegister, initRegisterListeners } from "./views/auth.js";
import { renderDashboard, initDashboardListeners } from "./views/dashboard.js";
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

const routes = {
  "/login": { render: renderLogin, init: initLoginListeners, public: true },
  "/register": { render: renderRegister, init: initRegisterListeners, public: true },
  "/dashboard": { render: renderDashboard, init: initDashboardListeners },
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
