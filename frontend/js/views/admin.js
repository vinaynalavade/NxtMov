import { api } from "../api.js";
import { showToast, createModal } from "../components.js";
import { getIcon } from "../icons.js";
import { ROLE_CONFIG } from "../permissions.js";

export function renderAdminView() {
  return `
    <div class="dashboard-container">
      <div class="dashboard-header" style="margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
          <div>
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
              <h1 class="view-title" style="margin: 0;">Administrator Governance Hub</h1>
              <span class="role-badge badge-admin">Administrator</span>
            </div>
            <p class="view-subtitle">Review mentor applications, audit users, manage institutional access, and govern platform security.</p>
          </div>
          <div style="display: flex; gap: 0.75rem;">
            <button id="btn-admin-invite" class="btn btn-primary" style="gap: 0.4rem; font-size: 0.85rem;">
              ${getIcon("plus", "", 14)} Invite Administrator / Mentor
            </button>
          </div>
        </div>
      </div>

      <!-- KPI Summary Cards -->
      <div class="kpi-grid" style="margin-bottom: 1.5rem;">
        <div class="card kpi-card">
          <div class="kpi-title" style="display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("shield-check", "", 15)} Pending Mentor Applications
          </div>
          <div id="admin-kpi-pending-apps" class="kpi-value" style="color: var(--warning-color);">-</div>
          <div class="kpi-caption">Awaiting administrator approval</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-title" style="display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("graduation-cap", "", 15)} Total Students
          </div>
          <div id="admin-kpi-students" class="kpi-value" style="color: #10b981;">-</div>
          <div class="kpi-caption">Active student accounts</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-title" style="display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("mentor", "", 15)} Approved Mentors
          </div>
          <div id="admin-kpi-mentors" class="kpi-value" style="color: #a855f7;">-</div>
          <div class="kpi-caption">Institutional faculty & guides</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-title" style="display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("users", "", 15)} Platform Users
          </div>
          <div id="admin-kpi-total-users" class="kpi-value" style="color: #3b82f6;">-</div>
          <div class="kpi-caption">All registered accounts</div>
        </div>
      </div>

      <!-- Admin Tabbed Navigation -->
      <div class="card" style="padding: 0; overflow: hidden; margin-bottom: 1.5rem;">
        <div class="profile-tabs" style="border-bottom: 1px solid var(--border-color); padding: 0.5rem 1rem 0 1rem; display: flex; gap: 0.5rem; background: var(--bg-secondary); overflow-x: auto;">
          <button class="profile-tab-btn active" data-tab="tab-mentor-apps" style="padding: 0.65rem 1rem; font-size: 0.875rem; font-weight: 600; background: none; border: none; cursor: pointer; border-bottom: 2px solid var(--primary-color); color: var(--primary-color);">
            Mentor Applications
          </button>
          <button class="profile-tab-btn" data-tab="tab-students" style="padding: 0.65rem 1rem; font-size: 0.875rem; font-weight: 600; background: none; border: none; cursor: pointer; color: var(--text-secondary);">
            Students
          </button>
          <button class="profile-tab-btn" data-tab="tab-mentors" style="padding: 0.65rem 1rem; font-size: 0.875rem; font-weight: 600; background: none; border: none; cursor: pointer; color: var(--text-secondary);">
            Mentors
          </button>
          <button class="profile-tab-btn" data-tab="tab-all-users" style="padding: 0.65rem 1rem; font-size: 0.875rem; font-weight: 600; background: none; border: none; cursor: pointer; color: var(--text-secondary);">
            Users & Account Types
          </button>
        </div>

        <!-- Tab 1: Mentor Applications -->
        <div id="tab-mentor-apps" class="admin-tab-content" style="padding: 1.5rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 0.75rem;">
            <div>
              <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin: 0;">Mentor Applications Review</h3>
              <p style="font-size: 0.8rem; color: var(--text-muted); margin: 0.2rem 0 0 0;">Inspect faculty credentials, approve active access, or reject ineligible submissions.</p>
            </div>
            <div style="display: flex; gap: 0.5rem;">
              <select id="mentor-app-filter" class="form-control" style="font-size: 0.8rem; padding: 0.35rem 0.65rem;">
                <option value="PENDING" selected>Pending Review</option>
                <option value="APPROVED">Approved</option>
                <option value="REJECTED">Rejected</option>
                <option value="">All Applications</option>
              </select>
            </div>
          </div>
          <div id="mentor-apps-table-container">
            <div style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading applications...</div>
          </div>
        </div>

        <!-- Tab 2: Students -->
        <div id="tab-students" class="admin-tab-content" style="padding: 1.5rem; display: none;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 0.75rem;">
            <div>
              <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin: 0;">Registered Students</h3>
              <p style="font-size: 0.8rem; color: var(--text-muted); margin: 0.2rem 0 0 0;">Career profile completeness, resumes, and candidate status.</p>
            </div>
          </div>
          <div id="students-table-container">
            <div style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading students...</div>
          </div>
        </div>

        <!-- Tab 3: Mentors -->
        <div id="tab-mentors" class="admin-tab-content" style="padding: 1.5rem; display: none;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 0.75rem;">
            <div>
              <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin: 0;">Approved Faculty Mentors</h3>
              <p style="font-size: 0.8rem; color: var(--text-muted); margin: 0.2rem 0 0 0;">Institutes, departments, and active mentoring faculty.</p>
            </div>
          </div>
          <div id="mentors-table-container">
            <div style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading mentors...</div>
          </div>
        </div>

        <!-- Tab 4: Users & Roles -->
        <div id="tab-all-users" class="admin-tab-content" style="padding: 1.5rem; display: none;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 0.75rem;">
            <div>
              <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin: 0;">Platform User Governance</h3>
              <p style="font-size: 0.8rem; color: var(--text-muted); margin: 0.2rem 0 0 0;">Audit accounts, inspect backend account types, and adjust account lifecycle statuses.</p>
            </div>
          </div>
          <div id="users-table-container">
            <div style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading users...</div>
          </div>
        </div>
      </div>
    </div>
  `;
}

export function initAdminListeners() {
  loadAdminStats();
  loadMentorApplications();

  // Tab switching
  document.querySelectorAll(".profile-tab-btn").forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll(".profile-tab-btn").forEach(b => {
        b.classList.remove("active");
        b.style.borderBottom = "none";
        b.style.color = "var(--text-secondary)";
      });
      document.querySelectorAll(".admin-tab-content").forEach(c => c.style.display = "none");

      btn.classList.add("active");
      btn.style.borderBottom = "2px solid var(--primary-color)";
      btn.style.color = "var(--primary-color)";

      const targetId = btn.getAttribute("data-tab");
      const targetEl = document.getElementById(targetId);
      if (targetEl) targetEl.style.display = "block";

      if (targetId === "tab-mentor-apps") loadMentorApplications();
      else if (targetId === "tab-students") loadStudents();
      else if (targetId === "tab-mentors") loadMentors();
      else if (targetId === "tab-all-users") loadAllUsers();
    };
  });

  // Filter change
  const filterSelect = document.getElementById("mentor-app-filter");
  if (filterSelect) {
    filterSelect.onchange = () => loadMentorApplications(filterSelect.value);
  }

  // Invite button
  document.getElementById("btn-admin-invite")?.addEventListener("click", openAdminInviteModal);
}

async function loadAdminStats() {
  try {
    const stats = await api.get("/admin/stats");
    const kpiPending = document.getElementById("admin-kpi-pending-apps");
    const kpiStudents = document.getElementById("admin-kpi-students");
    const kpiMentors = document.getElementById("admin-kpi-mentors");
    const kpiTotal = document.getElementById("admin-kpi-total-users");

    if (kpiPending) kpiPending.textContent = stats.pending_mentor_applications ?? 0;
    if (kpiStudents) kpiStudents.textContent = stats.total_students ?? 0;
    if (kpiMentors) kpiMentors.textContent = stats.total_mentors ?? 0;
    if (kpiTotal) kpiTotal.textContent = stats.total_users ?? 0;
  } catch (err) {
    console.warn("Failed to load admin stats:", err);
  }
}

async function loadMentorApplications(statusFilter = "PENDING") {
  const container = document.getElementById("mentor-apps-table-container");
  if (!container) return;

  try {
    const url = statusFilter ? `/admin/mentor-applications?status=${statusFilter}` : "/admin/mentor-applications";
    const apps = await api.get(url);

    if (!apps || apps.length === 0) {
      container.innerHTML = `<div style="text-align: center; padding: 2.5rem; color: var(--text-muted);">No mentor applications found for this filter.</div>`;
      return;
    }

    container.innerHTML = `
      <div class="table-responsive">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left;">
          <thead>
            <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-secondary);">
              <th style="padding: 0.75rem;">APPLICANT</th>
              <th style="padding: 0.75rem;">INSTITUTE & EMPLOYEE ID</th>
              <th style="padding: 0.75rem;">DEPARTMENT & DESIGNATION</th>
              <th style="padding: 0.75rem;">STATUS</th>
              <th style="padding: 0.75rem;">SUBMITTED</th>
              <th style="padding: 0.75rem; text-align: right;">ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            ${apps.map(a => {
              const statusBadge = a.status === "APPROVED" ? "badge-success" : (a.status === "REJECTED" ? "badge-danger" : "badge-warning");
              return `
                <tr style="border-bottom: 1px solid var(--border-color);">
                  <td style="padding: 0.75rem;">
                    <div style="font-weight: 700; color: var(--text-primary);">${a.full_name}</div>
                    <div style="font-size: 0.775rem; color: var(--text-muted);">${a.official_email}</div>
                  </td>
                  <td style="padding: 0.75rem;">
                    <div>${a.institute_name}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); font-family: monospace;">ID: ${a.employee_id}</div>
                  </td>
                  <td style="padding: 0.75rem;">
                    <div>${a.department || '—'}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${a.designation || 'Mentor'}</div>
                  </td>
                  <td style="padding: 0.75rem;">
                    <span class="badge-status ${statusBadge}" style="font-size: 0.675rem;">${a.status}</span>
                  </td>
                  <td style="padding: 0.75rem; font-size: 0.775rem; color: var(--text-muted);">
                    ${new Date(a.submitted_at).toLocaleDateString()}
                  </td>
                  <td style="padding: 0.75rem; text-align: right;">
                    <div style="display: inline-flex; gap: 0.4rem;">
                      ${a.status === "PENDING" ? `
                        <button class="btn btn-primary approve-mentor-btn" data-id="${a.id}" data-name="${a.full_name}" style="font-size: 0.75rem; padding: 0.25rem 0.55rem; background: #10b981; border-color: #10b981;">
                          Approve
                        </button>
                        <button class="btn btn-outline reject-mentor-btn" data-id="${a.id}" data-name="${a.full_name}" style="font-size: 0.75rem; padding: 0.25rem 0.55rem; color: #ef4444;">
                          Reject
                        </button>
                      ` : `
                        <button class="btn btn-outline view-app-btn" data-id="${a.id}" style="font-size: 0.75rem; padding: 0.25rem 0.55rem;">
                          Details
                        </button>
                      `}
                    </div>
                  </td>
                </tr>
              `;
            }).join("")}
          </tbody>
        </table>
      </div>
    `;

    // Attach Approve Listeners
    container.querySelectorAll(".approve-mentor-btn").forEach(btn => {
      btn.onclick = async () => {
        const id = btn.dataset.id;
        const name = btn.dataset.name;
        if (!confirm(`Approve mentor application for ${name}? This will activate their Mentor account.`)) return;

        try {
          await api.post(`/admin/mentor-applications/${id}/approve`);
          showToast(`Mentor application for ${name} approved successfully!`, "success");
          loadAdminStats();
          loadMentorApplications(document.getElementById("mentor-app-filter")?.value || "PENDING");
        } catch (err) {
          showToast(err.message || "Failed to approve application.", "danger");
        }
      };
    });

    // Attach Reject Listeners
    container.querySelectorAll(".reject-mentor-btn").forEach(btn => {
      btn.onclick = () => {
        const id = btn.dataset.id;
        const name = btn.dataset.name;
        openRejectModal(id, name);
      };
    });

    // View Details Listeners
    container.querySelectorAll(".view-app-btn").forEach(btn => {
      btn.onclick = async () => {
        const id = btn.dataset.id;
        const app = await api.get(`/admin/mentor-applications/${id}`);
        openAppDetailsModal(app);
      };
    });

  } catch (err) {
    container.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--danger-color);">${err.message || 'Failed to load applications.'}</div>`;
  }
}

function openRejectModal(appId, applicantName) {
  const content = `
    <form id="reject-app-form" style="display: flex; flex-direction: column; gap: 1rem;">
      <p style="font-size: 0.875rem; color: var(--text-secondary); margin: 0;">
        You are rejecting the application from <strong>${applicantName}</strong>. Please provide a clear reason that will be displayed upon login.
      </p>
      <div class="form-group">
        <label style="font-size: 0.85rem; font-weight: 600;">Rejection Reason *</label>
        <textarea id="reject-reason-input" class="form-control" rows="3" required placeholder="e.g. Official institutional credentials could not be verified with university faculty registry."></textarea>
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 0.75rem;">
        <button type="button" class="btn btn-outline close-modal-btn">Cancel</button>
        <button type="submit" class="btn btn-primary" style="background: #ef4444; border-color: #ef4444;">
          Confirm Rejection
        </button>
      </div>
    </form>
  `;

  const { closeModal } = createModal(`Reject Application: ${applicantName}`, content);

  document.getElementById("reject-app-form").onsubmit = async (e) => {
    e.preventDefault();
    const reason = document.getElementById("reject-reason-input").value.trim();
    if (!reason) return;

    try {
      await api.post(`/admin/mentor-applications/${appId}/reject`, { rejection_reason: reason });
      showToast(`Application for ${applicantName} has been rejected.`, "info");
      closeModal();
      loadAdminStats();
      loadMentorApplications(document.getElementById("mentor-app-filter")?.value || "PENDING");
    } catch (err) {
      showToast(err.message || "Failed to reject application.", "danger");
    }
  };
}

function openAppDetailsModal(app) {
  const content = `
    <div style="display: flex; flex-direction: column; gap: 1rem; font-size: 0.9rem;">
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; background: var(--bg-secondary); padding: 1rem; border-radius: var(--radius-md);">
        <div><strong>Applicant Name:</strong> ${app.full_name}</div>
        <div><strong>Official Email:</strong> ${app.official_email}</div>
        <div><strong>Institute / Univ:</strong> ${app.institute_name}</div>
        <div><strong>Employee ID:</strong> ${app.employee_id}</div>
        <div><strong>Department:</strong> ${app.department || '—'}</div>
        <div><strong>Designation:</strong> ${app.designation || 'Mentor'}</div>
        <div><strong>Status:</strong> <span class="badge-status badge-info">${app.status}</span></div>
        <div><strong>Submitted At:</strong> ${new Date(app.submitted_at).toLocaleString()}</div>
      </div>
      ${app.rejection_reason ? `
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger-color); padding: 0.75rem 1rem; border-radius: var(--radius-md); color: var(--danger-color);">
          <strong>Rejection Reason:</strong> ${app.rejection_reason}
        </div>
      ` : ''}
      <div style="display: flex; justify-content: flex-end;">
        <button type="button" class="btn btn-primary close-modal-btn">Close</button>
      </div>
    </div>
  `;
  createModal(`Application Details: ${app.full_name}`, content);
}

async function loadStudents() {
  const container = document.getElementById("students-table-container");
  if (!container) return;

  try {
    const students = await api.get("/admin/students");
    if (!students || students.length === 0) {
      container.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--text-muted);">No student accounts found.</div>`;
      return;
    }

    container.innerHTML = `
      <div class="table-responsive">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left;">
          <thead>
            <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-secondary);">
              <th style="padding: 0.75rem;">STUDENT NAME</th>
              <th style="padding: 0.75rem;">EMAIL & PHONE</th>
              <th style="padding: 0.75rem;">PROFILE COMPLETENESS</th>
              <th style="padding: 0.75rem;">RESUMES / APPS</th>
              <th style="padding: 0.75rem;">STATUS</th>
            </tr>
          </thead>
          <tbody>
            ${students.map(s => `
              <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem; font-weight: 600; color: var(--text-primary);">${s.full_name}</td>
                <td style="padding: 0.75rem;">
                  <div>${s.email}</div>
                  <div style="font-size: 0.75rem; color: var(--text-muted);">${s.phone || '—'}</div>
                </td>
                <td style="padding: 0.75rem;">
                  <div style="font-weight: 700; color: ${s.completeness_score >= 80 ? 'var(--accent-color)' : 'var(--warning-color)'};">${s.completeness_score}%</div>
                </td>
                <td style="padding: 0.75rem; font-size: 0.8rem; color: var(--text-muted);">
                  📄 ${s.resumes_count} Resumes • 🎯 ${s.applications_count} Apps
                </td>
                <td style="padding: 0.75rem;">
                  <span class="badge-status badge-success" style="font-size: 0.675rem;">${s.status}</span>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--danger-color);">${err.message}</div>`;
  }
}

async function loadMentors() {
  const container = document.getElementById("mentors-table-container");
  if (!container) return;

  try {
    const mentors = await api.get("/admin/mentors");
    if (!mentors || mentors.length === 0) {
      container.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--text-muted);">No approved mentors found.</div>`;
      return;
    }

    container.innerHTML = `
      <div class="table-responsive">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left;">
          <thead>
            <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-secondary);">
              <th style="padding: 0.75rem;">MENTOR NAME</th>
              <th style="padding: 0.75rem;">EMAIL</th>
              <th style="padding: 0.75rem;">INSTITUTE & DEPT</th>
              <th style="padding: 0.75rem;">STATUS</th>
            </tr>
          </thead>
          <tbody>
            ${mentors.map(m => `
              <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 0.75rem; font-weight: 600; color: var(--text-primary);">${m.full_name}</td>
                <td style="padding: 0.75rem;">${m.email}</td>
                <td style="padding: 0.75rem;">
                  <div>${m.institute_name}</div>
                  <div style="font-size: 0.75rem; color: var(--text-muted);">${m.department} (${m.designation})</div>
                </td>
                <td style="padding: 0.75rem;">
                  <span class="badge-status badge-mentor" style="font-size: 0.675rem;">ACTIVE MENTOR</span>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--danger-color);">${err.message}</div>`;
  }
}

async function loadAllUsers() {
  const container = document.getElementById("users-table-container");
  if (!container) return;

  try {
    const users = await api.get("/admin/users");
    if (!users || users.length === 0) {
      container.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--text-muted);">No users found.</div>`;
      return;
    }

    container.innerHTML = `
      <div class="table-responsive">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left;">
          <thead>
            <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-secondary);">
              <th style="padding: 0.75rem;">USER NAME</th>
              <th style="padding: 0.75rem;">EMAIL</th>
              <th style="padding: 0.75rem;">ACCOUNT TYPE (SOURCE OF TRUTH)</th>
              <th style="padding: 0.75rem;">STATUS</th>
              <th style="padding: 0.75rem;">JOINED</th>
            </tr>
          </thead>
          <tbody>
            ${users.map(u => {
              const rMeta = ROLE_CONFIG[u.account_type] || ROLE_CONFIG.STUDENT;
              return `
                <tr style="border-bottom: 1px solid var(--border-color);">
                  <td style="padding: 0.75rem; font-weight: 600; color: var(--text-primary);">${u.full_name}</td>
                  <td style="padding: 0.75rem;">${u.email}</td>
                  <td style="padding: 0.75rem;">
                    <span class="role-badge ${rMeta.badgeClass}">${rMeta.title}</span>
                  </td>
                  <td style="padding: 0.75rem;">
                    <span class="badge-status ${u.status === 'ACTIVE' ? 'badge-success' : 'badge-warning'}" style="font-size: 0.675rem;">${u.status}</span>
                  </td>
                  <td style="padding: 0.75rem; font-size: 0.75rem; color: var(--text-muted);">
                    ${new Date(u.created_at).toLocaleDateString()}
                  </td>
                </tr>
              `;
            }).join("")}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--danger-color);">${err.message}</div>`;
  }
}

function openAdminInviteModal() {
  const content = `
    <form id="admin-invite-form" style="display: flex; flex-direction: column; gap: 1rem;">
      <div class="form-group">
        <label style="font-size: 0.85rem; font-weight: 600;">Member Email Address *</label>
        <input type="email" id="admin-inv-email" required placeholder="colleague@institution.edu" class="form-control" />
      </div>
      <div class="form-group">
        <label style="font-size: 0.85rem; font-weight: 600;">Full Name</label>
        <input type="text" id="admin-inv-name" placeholder="Prof. Sharma" class="form-control" />
      </div>
      <div class="form-group">
        <label style="font-size: 0.85rem; font-weight: 600;">Account Type *</label>
        <select id="admin-inv-role" class="form-control" required>
          <option value="ADMIN">Administrator (Full Platform Control)</option>
          <option value="MENTOR">Mentor (Direct Approval)</option>
        </select>
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 0.5rem;">
        <button type="button" class="btn btn-outline close-modal-btn">Cancel</button>
        <button type="submit" class="btn btn-primary">Send Invitation</button>
      </div>
    </form>
  `;

  const { closeModal } = createModal("Invite Administrator or Mentor", content);

  document.getElementById("admin-invite-form").onsubmit = async (e) => {
    e.preventDefault();
    const email = document.getElementById("admin-inv-email").value.trim();
    const full_name = document.getElementById("admin-inv-name").value.trim();
    const account_type = document.getElementById("admin-inv-role").value;

    try {
      const res = await api.post("/admin/invite", { email, full_name, account_type });
      showToast(res.message || `Invited ${email}!`, "success");
      closeModal();
      loadAdminStats();
    } catch (err) {
      showToast(err.message || "Failed to invite user.", "danger");
    }
  };
}
