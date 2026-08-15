import { api } from "./api.js";
import { store } from "./store.js";
import { Router } from "./router.js";
import { showToast, createModal } from "./components.js";
import { initSidebar, renderSidebarNav } from "./sidebar.js";
import { getIcon } from "./icons.js";

/* ================================================================
   APP INITIALIZATION — Single Entry Point
   ================================================================ */
document.addEventListener("DOMContentLoaded", async () => {
  console.log("NxtMov SPA v2.0 Initializing...");

  try {
    // 1. Theme toggle (must run before any rendering)
    initThemeToggle();

    // 2. Sidebar controller (single authoritative init)
    initSidebar();

    // 3. Session validation & workspace setup
    const token = api.getToken();
    if (token) {
      try {
        const data = await api.get("/auth/me");
        store.setState({ user: data.user, organizations: data.organizations });
        renderSidebarNav();
      } catch (e) {
        console.warn("Session validation notice:", e);
        api.clearToken();
        renderSidebarNav();
      }

      // Workspace switcher (safe init)
      try { await loadWorkspaceSwitcher(); } catch (err) {
        console.warn("Workspace switcher init notice:", err);
      }

      // Notification bell (safe init)
      try { await initNotificationBell(); } catch (err) {
        console.warn("Notification bell init notice:", err);
      }
    } else {
      renderSidebarNav();
    }

    // 4. Global logout handler — single source of truth
    const performLogout = () => {
      api.clearToken();
      store.setState({ user: null, organizations: [] });
      showToast("Logged out successfully.");
      renderSidebarNav();
      window.location.hash = "#/login";
      Router.handleRoute();
    };

    // Sidebar logout button is the primary logout control
    document.getElementById("sidebar-logout-btn")?.addEventListener("click", performLogout);

    // 5. Create workspace/consultancy button
    document.getElementById("create-consultancy-btn")?.addEventListener("click", openCreateWorkspaceModal);

    // 6. Initialize SPA Router
    Router.init();

  } catch (startupError) {
    console.error("CRITICAL: SPA Startup Exception:", startupError);
    const mainContent = document.getElementById("main-content");
    if (mainContent) {
      mainContent.innerHTML = `
        <div class="card" style="max-width: 520px; margin: 4rem auto; padding: 2rem; text-align: center; border-left: 4px solid var(--danger-color);">
          <h3 style="color: var(--danger-color); font-weight: 700; margin-bottom: 0.5rem;">Application Load Error</h3>
          <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1.25rem;">
            ${startupError.message || startupError}
          </p>
          <button onclick="window.location.reload()" class="btn btn-primary">↻ Reload</button>
        </div>
      `;
    }
  }
});

/* ================================================================
   THEME TOGGLE — Single handler
   ================================================================ */
function initThemeToggle() {
  const toggleBtn = document.getElementById("theme-toggle-btn");
  const toggleIcon = document.getElementById("theme-toggle-icon");

  const updateUI = (theme) => {
    if (toggleIcon) toggleIcon.innerHTML = theme === "dark" ? getIcon("sun", "", 18) : getIcon("moon", "", 18);
    if (toggleBtn) toggleBtn.title = theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode";
  };

  const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
  updateUI(currentTheme);

  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const activeTheme = document.documentElement.getAttribute("data-theme");
      const nextTheme = activeTheme === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", nextTheme);
      localStorage.setItem("nxtmov_theme", nextTheme);
      updateUI(nextTheme);
    });
  }
}

/* ================================================================
   WORKSPACE SWITCHER
   ================================================================ */
async function loadWorkspaceSwitcher() {
  const mount = document.getElementById("workspace-mount");
  const bar = document.getElementById("user-profile-bar");
  if (!mount || !bar) return;

  const token = api.getToken();
  if (!token) {
    bar.style.display = "none";
    return;
  }

  try {
    bar.style.display = "flex";
    const data = await api.get("/auth/me");
    const workspaces = data.organizations || [];

    // Parse active organization ID from JWT token payload
    let activeOrgId = null;
    try {
      const parts = token.split(".");
      if (parts.length === 3) {
        const payload = JSON.parse(atob(parts[1]));
        activeOrgId = payload.org_id;
      }
    } catch (e) {
      console.warn("Token payload parse notice:", e);
    }

    if (workspaces.length <= 1) {
      // Exactly 1 workspace: Render simple non-dropdown badge
      const singleOrg = workspaces[0] || { name: "Personal", type: "INDIVIDUAL" };
      const displayName = singleOrg.type === "INDIVIDUAL" ? "Personal" : singleOrg.name;
      mount.innerHTML = `
        <span class="workspace-single-badge" title="Active Workspace">
          ${getIcon(singleOrg.type === "INDIVIDUAL" ? "user" : "briefcase", "", 14)}
          <span>${displayName}</span>
        </span>
      `;
    } else {
      // Multiple workspaces: Render interactive dropdown selector
      mount.innerHTML = `
        <select id="workspace-switcher" class="workspace-dropdown-select" aria-label="Select Active Workspace">
          ${workspaces.map(w => {
            const isSelected = activeOrgId ? w.id === activeOrgId : false;
            const label = w.type === 'INDIVIDUAL' ? 'Personal' : w.name;
            return `<option value="${w.id}" ${isSelected ? 'selected' : ''}>${label}</option>`;
          }).join("")}
        </select>
      `;

      const switcher = document.getElementById("workspace-switcher");
      if (switcher) {
        switcher.onchange = async (e) => {
          const orgId = parseInt(e.target.value);
          try {
            const res = await api.post(`/auth/switch?organization_id=${orgId}`);
            api.setToken(res.access_token);
            showToast("Workspace switched!");
            await loadWorkspaceSwitcher();
            renderSidebarNav();
            Router.handleRoute();
          } catch (err) {
            showToast(err.message || "Failed to switch workspace.", "danger");
          }
        };
      }
    }
  } catch (err) {
    console.warn("Failed to load workspaces:", err);
  }
}

/* ================================================================
   CREATE WORKSPACE MODAL (formerly "Create Consultancy")
   ================================================================ */
function openCreateWorkspaceModal() {
  const content = `
    <form id="create-consultancy-form" style="display: flex; flex-direction: column; gap: 1rem;">
      <div class="form-group">
        <label>Workspace / Agency Name *</label>
        <input type="text" id="consultancy-name" required placeholder="e.g. Apex Recruitment Partners" class="form-control" />
      </div>
      <div class="form-group">
        <label>Contact Phone</label>
        <input type="text" id="consultancy-phone" placeholder="+91 80 1234 5678" class="form-control" />
      </div>
      <div class="form-group">
        <label>Website URL</label>
        <input type="url" id="consultancy-website" placeholder="https://apexrecruiters.com" class="form-control" />
      </div>
      <div class="form-group">
        <label>Location / City</label>
        <input type="text" id="consultancy-location" placeholder="Bengaluru, India" class="form-control" />
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 0.5rem;">
        <button type="button" class="btn btn-outline close-modal-btn">Cancel</button>
        <button type="submit" class="btn btn-primary">Create Workspace</button>
      </div>
    </form>
  `;

  const { closeModal } = createModal("Create Workspace", content);

  document.getElementById("create-consultancy-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("consultancy-name").value.trim();
    const phone = document.getElementById("consultancy-phone").value.trim();
    const website = document.getElementById("consultancy-website").value.trim();
    const location = document.getElementById("consultancy-location").value.trim();

    try {
      const newOrg = await api.post("/organizations", { name, phone, website, location, type: "CONSULTANCY" });
      showToast(`Created workspace "${name}"!`);

      const res = await api.post(`/auth/switch?organization_id=${newOrg.id}`);
      api.setToken(res.access_token);

      closeModal();
      loadWorkspaceSwitcher();
      renderSidebarNav();
      Router.handleRoute();
    } catch (err) {
      showToast(err.message || "Failed to create workspace.", "danger");
    }
  });
}

/* ================================================================
   NOTIFICATION BELL — Single handler
   ================================================================ */
async function initNotificationBell() {
  const container = document.getElementById("notification-bell-container");
  const bellBtn = document.getElementById("notif-bell-btn");
  const badge = document.getElementById("unread-notif-badge");
  const dropdown = document.getElementById("notif-dropdown");
  const listContainer = document.getElementById("notif-list-container");
  const markAllBtn = document.getElementById("mark-all-read-btn");

  if (!container || !bellBtn) return;
  container.style.display = "block";

  const fetchAndRender = async () => {
    try {
      const res = await api.get("/notifications");
      if (badge) {
        if (res && res.unread_count > 0) {
          badge.style.display = "inline-block";
          badge.textContent = res.unread_count > 99 ? "99+" : res.unread_count;
        } else {
          badge.style.display = "none";
        }
      }

      if (listContainer) {
        if (!res || !res.notifications || res.notifications.length === 0) {
          listContainer.innerHTML = `<div style="text-align: center; color: var(--text-muted); font-size: 0.8rem; padding: 1.5rem;">No notifications right now.</div>`;
        } else {
          listContainer.innerHTML = res.notifications.map(n => `
            <div class="notif-item ${n.is_read ? '' : 'unread'}" data-notif-id="${n.id}" data-link="${n.link_url || ''}">
              <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.1rem; font-size: 0.8rem;">${n.title}</div>
              <div style="color: var(--text-secondary); line-height: 1.3; font-size: 0.775rem;">${n.message}</div>
              <div style="font-size: 0.675rem; color: var(--text-muted); margin-top: 0.2rem;">${new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
            </div>
          `).join("");

          listContainer.querySelectorAll(".notif-item").forEach(item => {
            item.addEventListener("click", async () => {
              const id = item.dataset.notifId;
              const link = item.dataset.link;
              try {
                if (item.classList.contains("unread")) {
                  await api.patch(`/notifications/${id}/read`);
                }
                if (link) window.location.hash = link;
              } catch (e) {
                console.warn("Notification click notice:", e);
              }
              dropdown.classList.remove("visible");
              fetchAndRender();
            });
          });
        }
      }
    } catch (err) {
      console.warn("Failed to load notifications:", err);
      if (listContainer) {
        listContainer.innerHTML = `<div style="text-align: center; color: var(--text-muted); font-size: 0.8rem; padding: 1.5rem;">Notifications unavailable.</div>`;
      }
    }
  };

  // Bell toggle with CSS class instead of inline style
  bellBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isVisible = dropdown.classList.contains("visible");
    dropdown.classList.toggle("visible", !isVisible);
    if (!isVisible) fetchAndRender();
  });

  // Close dropdown on outside click (single listener)
  document.addEventListener("click", (e) => {
    if (dropdown && !container.contains(e.target)) {
      dropdown.classList.remove("visible");
    }
  });

  // Mark all read
  if (markAllBtn) {
    markAllBtn.addEventListener("click", async (e) => {
      e.stopPropagation();
      try {
        await api.post("/notifications/read-all");
        showToast("All notifications marked as read.");
        fetchAndRender();
      } catch (err) {
        showToast("Failed to mark notifications read.", "danger");
      }
    });
  }

  fetchAndRender();
}
