import { api, API } from "../api.js";
import { store } from "../store.js";
import { showToast, createModal } from "../components.js";
import { getUserRole } from "../sidebar.js";
import { getIcon } from "../icons.js";

export function renderDashboard() {
  const role = getUserRole();
  const user = store.getState().user || { full_name: "User" };
  const firstName = user.full_name ? user.full_name.split(" ")[0] : "User";

  if (role === "ADMIN") {
    return renderAdminDashboard(firstName);
  } else if (role === "RECRUITER") {
    return renderRecruiterDashboard(firstName);
  } else if (role === "MENTOR" || role === "COUNSELOR") {
    return renderMentorDashboard(firstName);
  }
  return renderStudentDashboard(firstName);
}

/* ================================================================
   1. STUDENT CAREER DASHBOARD
   ================================================================ */
function renderStudentDashboard(firstName) {
  return `
    <div class="dashboard-container">
      <div class="dashboard-header" style="margin-bottom: 1.5rem;">
        <h1 class="view-title">Welcome back, ${firstName}!</h1>
        <p class="view-subtitle">Your personal career acceleration command center. Track your ATS score, apply to matched roles, and complete next actions.</p>
      </div>

      <!-- Profile & ATS Quick Status Banner -->
      <div id="dash-profile-banner" class="card" style="margin-bottom: 1.5rem; background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1.25rem;">
          <div>
            <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.2rem; display: flex; align-items: center; gap: 0.4rem;">
              ${getIcon("target", "", 16)} Talent Profile & ATS Status
            </h3>
            <p id="dash-profile-status-sub" style="font-size: 0.8rem; color: var(--text-muted); margin: 0;">Loading completeness & ATS analytics...</p>
          </div>
          <div style="display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap;">
            <a href="#/resume" class="btn btn-primary" style="font-size: 0.8rem; gap: 0.4rem;">
              ${getIcon("resume", "", 15)} NxtMov ATS Analyzer
            </a>
            <a href="#/profile" class="btn btn-outline" style="font-size: 0.8rem; gap: 0.4rem;">
              ${getIcon("user", "", 15)} Edit Profile
            </a>
          </div>
        </div>
      </div>

      <!-- KPI Grid Cards -->
      <div class="kpi-grid" style="margin-bottom: 1.5rem;">
        <div class="card kpi-card">
          <div class="kpi-title" style="display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("award", "", 15)} NxtMov ATS Score
          </div>
          <div id="kpi-ats-score" class="kpi-value" style="color: var(--primary-color);">--</div>
          <div class="kpi-caption">Resume intelligence score</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-title" style="display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("target", "", 15)} Matched Roles
          </div>
          <div id="kpi-opportunities" class="kpi-value" style="color: var(--accent-color);">-</div>
          <div class="kpi-caption">Based on your skills</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-title" style="display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("applications", "", 15)} Applications
          </div>
          <div id="kpi-applications" class="kpi-value" style="color: #3B82F6;">-</div>
          <div class="kpi-caption">Active submissions & interviews</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-title" style="display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("clock", "", 15)} Next Actions
          </div>
          <div id="kpi-today" class="kpi-value" style="color: var(--warning-color);">-</div>
          <div class="kpi-caption">Follow-ups due today</div>
        </div>
      </div>

      <!-- Recommended Jobs Preview -->
      <div class="card" style="margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;">
          <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 0.4rem;">
            ${getIcon("target", "", 16)} Recommended Roles For You
          </h3>
          <a href="#/recommendations" class="btn btn-outline" style="font-size: 0.75rem; gap: 0.3rem;">
            View All Matches ${getIcon("chevron-right", "", 13)}
          </a>
        </div>
        <div id="dash-recs-preview" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem;">
          <div style="color: var(--text-muted); font-size: 0.85rem; padding: 1.5rem; text-align: center; grid-column: 1 / -1;">Loading recommendations...</div>
        </div>
      </div>

      <!-- Next Moves Engine & Quick Actions -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem; align-items: start;">
        <div class="card">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
            <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 0.4rem;">
              ${getIcon("sparkles", "", 16)} YOUR NEXT MOVES (ACTION ENGINE)
            </h3>
            <a href="#/followups" class="btn btn-outline" style="font-size: 0.75rem;">View All</a>
          </div>
          <div id="dashboard-followups-list">
            <p style="color: var(--text-muted); font-size: 0.85rem; text-align: center; padding: 1.5rem 0;">Loading action items...</p>
          </div>
        </div>

        <div class="card">
          <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.4rem;">
            ${getIcon("rocket", "", 16)} QUICK ACTIONS
          </h3>
          <div style="display: flex; flex-direction: column; gap: 0.65rem;">
            <button id="btn-quick-log-hr" class="btn btn-primary" style="justify-content: start; gap: 0.5rem;">
              ${getIcon("phone", "", 16)} Log Interaction / Call
            </button>
            <a href="#/resume" class="btn btn-outline" style="justify-content: start; gap: 0.5rem;">
              ${getIcon("resume", "", 16)} NxtMov ATS Score & Resume Parser
            </a>
            <a href="#/recommendations" class="btn btn-outline" style="justify-content: start; gap: 0.5rem;">
              ${getIcon("recommendations", "", 16)} Role Matching Engine
            </a>
            <a href="#/profile" class="btn btn-outline" style="justify-content: start; gap: 0.5rem;">
              ${getIcon("user", "", 16)} Edit Profile & Skills
            </a>
          </div>
        </div>
      </div>
    </div>
  `;
}

/* ================================================================
   2. WORKSPACE ADMINISTRATOR DASHBOARD
   ================================================================ */
function renderAdminDashboard(firstName) {
  return `
    <div class="dashboard-container">
      <div class="dashboard-header" style="margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
          <div>
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
              <h1 class="view-title" style="margin: 0;">Administrator Command Center</h1>
              <span class="role-badge badge-admin">Administrator</span>
            </div>
            <p class="view-subtitle">Platform governance: Approve mentor applications, oversee student career progress, audit accounts, and manage organization settings.</p>
          </div>
          <div style="display: flex; gap: 0.75rem;">
            <a href="#/admin" class="btn btn-primary" style="font-size: 0.85rem; gap: 0.4rem;">
              ${getIcon("shield-check", "", 15)} Open Governance Portal
            </a>
          </div>
        </div>
      </div>

      <!-- Admin KPI Grid -->
      <div class="kpi-grid" style="margin-bottom: 1.5rem;">
        <div class="card kpi-card">
          <div class="kpi-title" style="display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("shield-check", "", 15)} Pending Mentor Applications
          </div>
          <div id="kpi-admin-pending" class="kpi-value" style="color: var(--warning-color);">-</div>
          <div class="kpi-caption">Awaiting verification</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-title" style="display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("graduation-cap", "", 15)} Total Students
          </div>
          <div id="kpi-admin-students" class="kpi-value" style="color: #10b981;">-</div>
          <div class="kpi-caption">Active student accounts</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-title" style="display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("mentor", "", 15)} Approved Mentors
          </div>
          <div id="kpi-admin-mentors" class="kpi-value" style="color: #a855f7;">-</div>
          <div class="kpi-caption">Faculty & guides</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-title" style="display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("users", "", 15)} Platform Users
          </div>
          <div id="kpi-admin-total" class="kpi-value" style="color: #3b82f6;">-</div>
          <div class="kpi-caption">Total registered users</div>
        </div>
      </div>

      <!-- Governance Quick Links & Admin Controls -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem; margin-bottom: 1.5rem; align-items: start;">
        <div class="card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 0.4rem;">
              ${getIcon("shield-check", "", 16)} Approvals & Applications
            </h3>
            <a href="#/admin" class="btn btn-outline" style="font-size: 0.75rem;">Manage All</a>
          </div>
          <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1rem;">
            Institutional faculty members apply for Mentor accounts. Administrators must verify credentials before access is granted.
          </p>
          <div style="display: flex; flex-direction: column; gap: 0.65rem;">
            <a href="#/admin-applications" class="btn btn-primary" style="justify-content: start; gap: 0.5rem;">
              ${getIcon("shield-check", "", 16)} Review Mentor Applications
            </a>
            <a href="#/admin-students" class="btn btn-outline" style="justify-content: start; gap: 0.5rem;">
              ${getIcon("graduation-cap", "", 16)} View Student Talent Directory
            </a>
            <a href="#/admin-mentors" class="btn btn-outline" style="justify-content: start; gap: 0.5rem;">
              ${getIcon("mentor", "", 16)} View Faculty Mentors
            </a>
          </div>
        </div>

        <div class="card">
          <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.4rem;">
            ${getIcon("team", "", 16)} PLATFORM & WORKSPACE CONTROLS
          </h3>
          <div style="display: flex; flex-direction: column; gap: 0.65rem;">
            <a href="#/admin-users" class="btn btn-outline" style="justify-content: start; gap: 0.5rem;">
              ${getIcon("users", "", 16)} Audit Users & Account Types
            </a>
            <a href="#/team" class="btn btn-outline" style="justify-content: start; gap: 0.5rem;">
              ${getIcon("team", "", 16)} Manage Organizations & Roles
            </a>
            <a href="#/opportunities" class="btn btn-outline" style="justify-content: start; gap: 0.5rem;">
              ${getIcon("opportunities", "", 16)} Manage Job Requirements
            </a>
            <a href="#/import" class="btn btn-outline" style="justify-content: start; gap: 0.5rem;">
              ${getIcon("import", "", 16)} Bulk Import Data (CSV/Excel)
            </a>
          </div>
        </div>
      </div>
    </div>
  `;
}

/* ================================================================
   3. RECRUITER / TALENT PARTNER DASHBOARD
   ================================================================ */
function renderRecruiterDashboard(firstName) {
  return `
    <div class="dashboard-container">
      <div class="dashboard-header" style="margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
          <h1 class="view-title" style="margin: 0;">Recruitment Desk</h1>
          <span class="role-badge badge-recruiter">Talent Partner</span>
        </div>
        <p class="view-subtitle">Candidate sourcing, talent matching, requirement tracking, and employer submissions.</p>
      </div>

      <!-- Recruiter KPI Grid -->
      <div class="kpi-grid" style="margin-bottom: 1.5rem;">
        <div class="card kpi-card">
          <div class="kpi-title" style="display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("candidates", "", 15)} Total Candidates
          </div>
          <div id="kpi-admin-candidates" class="kpi-value" style="color: var(--primary-color);">-</div>
          <div class="kpi-caption">Candidate roster pool</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-title" style="display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("opportunities", "", 15)} Open Requirements
          </div>
          <div id="kpi-opportunities" class="kpi-value" style="color: #3B82F6;">-</div>
          <div class="kpi-caption">Active client mandates</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-title" style="display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("submissions", "", 15)} Client Submissions
          </div>
          <div id="kpi-applications" class="kpi-value" style="color: var(--accent-color);">-</div>
          <div class="kpi-caption">Submissions & interviews</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-title" style="display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("followups", "", 15)} Follow-ups Due
          </div>
          <div id="kpi-today" class="kpi-value" style="color: var(--warning-color);">-</div>
          <div class="kpi-caption">Recruiter actions due today</div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem; margin-bottom: 1.5rem; align-items: start;">
        <div class="card">
          <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.4rem;">
            ${getIcon("rocket", "", 16)} RECRUITER ACTIONS
          </h3>
          <div style="display: flex; flex-direction: column; gap: 0.65rem;">
            <button id="btn-quick-log-hr" class="btn btn-primary" style="justify-content: start; gap: 0.5rem;">
              ${getIcon("phone", "", 16)} Log Client / HR Interaction
            </button>
            <a href="#/opportunities" class="btn btn-outline" style="justify-content: start; gap: 0.5rem;">
              ${getIcon("opportunities", "", 16)} Manage Job Requirements
            </a>
            <a href="#/import" class="btn btn-outline" style="justify-content: start; gap: 0.5rem;">
              ${getIcon("import", "", 16)} Bulk Import Candidates
            </a>
            <a href="#/contacts" class="btn btn-outline" style="justify-content: start; gap: 0.5rem;">
              ${getIcon("contacts", "", 16)} HR Contacts Directory
            </a>
          </div>
        </div>

        <div class="card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 0.4rem;">
              ${getIcon("chart", "", 16)} Candidate Pipeline Stages
            </h3>
            <a href="#/candidates" class="btn btn-outline" style="font-size: 0.75rem;">View Candidates</a>
          </div>
          <div id="admin-pipeline-stages" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem;">
            <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: var(--radius-md); text-align: center;">
              <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 600;">NEW / SOURCED</div>
              <div id="pipe-stage-new" style="font-size: 1.25rem; font-weight: 800; color: var(--text-primary); margin-top: 0.2rem;">-</div>
            </div>
            <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: var(--radius-md); text-align: center;">
              <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 600;">SCREENING</div>
              <div id="pipe-stage-screen" style="font-size: 1.25rem; font-weight: 800; color: var(--primary-color); margin-top: 0.2rem;">-</div>
            </div>
            <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: var(--radius-md); text-align: center;">
              <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 600;">INTERVIEWING</div>
              <div id="pipe-stage-interview" style="font-size: 1.25rem; font-weight: 800; color: var(--accent-color); margin-top: 0.2rem;">-</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Engine Follow-ups -->
      <div class="card">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
          <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 0.4rem;">
            ${getIcon("followups", "", 16)} SCHEDULED FOLLOW-UPS & NEXT MOVES
          </h3>
          <a href="#/followups" class="btn btn-outline" style="font-size: 0.75rem;">View All</a>
        </div>
        <div id="dashboard-followups-list">
          <p style="color: var(--text-muted); font-size: 0.85rem; text-align: center; padding: 1.5rem 0;">Loading action items...</p>
        </div>
      </div>
    </div>
  `;
}

/* ================================================================
   3. MENTOR / COUNSELOR DASHBOARD
   ================================================================ */
function renderMentorDashboard(firstName) {
  return `
    <div class="dashboard-container">
      <div class="dashboard-header" style="margin-bottom: 1.5rem;">
        <h1 class="view-title">Student Mentorship Hub</h1>
        <p class="view-subtitle">Guide students through resume improvements, mock interviews, and career placement journey.</p>
      </div>

      <div class="kpi-grid" style="margin-bottom: 1.5rem;">
        <div class="card kpi-card">
          <div class="kpi-title">Assigned Students</div>
          <div id="kpi-mentor-students" class="kpi-value" style="color: var(--primary-color);">-</div>
          <div class="kpi-caption">Active mentorship roster</div>
        </div>
        <div class="card kpi-card">
          <div class="kpi-title">Mock Interviews</div>
          <div id="kpi-applications" class="kpi-value" style="color: var(--accent-color);">-</div>
          <div class="kpi-caption">Scheduled practice sessions</div>
        </div>
        <div class="card kpi-card">
          <div class="kpi-title">Follow-ups Due</div>
          <div id="kpi-today" class="kpi-value" style="color: var(--warning-color);">-</div>
          <div class="kpi-caption">Guidance touchpoints</div>
        </div>
      </div>

      <div class="card">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
          <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary);">Student Guidance Actions</h3>
          <a href="#/mentor" class="btn btn-primary" style="font-size: 0.75rem;">View Student Roster</a>
        </div>
        <div id="dashboard-followups-list">
          <p style="color: var(--text-muted); font-size: 0.85rem; text-align: center; padding: 1.5rem 0;">Loading mentorship follow-ups...</p>
        </div>
      </div>
    </div>
  `;
}

export async function initDashboardListeners() {
  loadProfileBanner();
  loadRecommendedPreview();

  // Quick Log HR Interaction Button
  document.getElementById("btn-quick-log-hr")?.addEventListener("click", openLogHRInteractionModal);

  const role = getUserRole();
  if (role === "ADMIN") {
    try {
      const adminStats = await API.get("/admin/stats");
      const kpiPending = document.getElementById("kpi-admin-pending");
      const kpiStudents = document.getElementById("kpi-admin-students");
      const kpiMentors = document.getElementById("kpi-admin-mentors");
      const kpiTotal = document.getElementById("kpi-admin-total");

      if (kpiPending) kpiPending.textContent = adminStats.pending_mentor_applications ?? 0;
      if (kpiStudents) kpiStudents.textContent = adminStats.total_students ?? 0;
      if (kpiMentors) kpiMentors.textContent = adminStats.total_mentors ?? 0;
      if (kpiTotal) kpiTotal.textContent = adminStats.total_users ?? 0;
    } catch (err) {
      console.warn("Failed to load admin stats:", err);
    }
  }

  try {
    const stats = await API.get("/activity/dashboard/stats");

    const kpiToday = document.getElementById("kpi-today");
    const kpiOverdue = document.getElementById("kpi-overdue");
    const kpiOpps = document.getElementById("kpi-opportunities");
    const kpiApps = document.getElementById("kpi-applications");
    const kpiCand = document.getElementById("kpi-admin-candidates");
    const kpiMentor = document.getElementById("kpi-mentor-students");

    if (kpiToday) kpiToday.textContent = stats.followups_due_today ?? 0;
    if (kpiOverdue) kpiOverdue.textContent = stats.overdue_followups ?? 0;
    if (kpiOpps) kpiOpps.textContent = stats.active_opportunities ?? 0;
    if (kpiApps) kpiApps.textContent = `${stats.applications_count ?? 0} (${stats.interviews_count ?? 0} Interviews)`;
    if (kpiCand) kpiCand.textContent = stats.total_candidates ?? stats.applications_count ?? 0;
    if (kpiMentor) kpiMentor.textContent = stats.total_candidates ?? 0;

    const listContainer = document.getElementById("dashboard-followups-list");
    if (!stats.today_followups || stats.today_followups.length === 0) {
      if (listContainer) {
        listContainer.innerHTML = `
          <div class="empty-state" style="margin: 0.5rem 0; padding: 1.5rem 1rem; text-align: center;">
            <div style="color: var(--accent-color); margin-bottom: 0.5rem;">${getIcon("check-circle", "", 32)}</div>
            <div class="empty-state-title" style="font-weight: 700; margin-top: 0.25rem;">No pending follow-ups due today!</div>
            <div class="empty-state-description" style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.75rem;">Log recruiter calls or schedule your next move.</div>
            <button id="btn-dash-log-hr" class="btn btn-primary" style="font-size: 0.8rem; gap: 0.4rem;">
              ${getIcon("phone", "", 14)} Log Interaction
            </button>
          </div>
        `;
        document.getElementById("btn-dash-log-hr")?.addEventListener("click", openLogHRInteractionModal);
      }
      return;
    }

    const now = new Date();

    if (listContainer) {
      listContainer.innerHTML = stats.today_followups.map(item => {
        const isOverdue = new Date(item.due_date) < now;

        return `
          <div class="followup-item-row" style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.75rem; padding: 0.75rem 0; border-bottom: 1px solid var(--border-color);">
            <div style="flex: 1; min-width: 200px;">
              <div style="font-weight: 700; font-size: 0.9rem; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                <span>${item.title}</span>
                ${isOverdue ? '<span class="badge-status badge-danger" style="font-size: 0.65rem;">OVERDUE</span>' : '<span class="badge-status badge-warning" style="font-size: 0.65rem;">DUE TODAY</span>'}
              </div>
              <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.15rem; display: flex; align-items: center; gap: 0.3rem;">
                ${getIcon("clock", "", 12)} ${new Date(item.due_date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
              </div>
            </div>

            <div style="display: flex; gap: 0.4rem; align-items: center;">
              <button class="btn btn-primary complete-followup-btn" data-id="${item.id}" style="font-size: 0.75rem; padding: 0.25rem 0.6rem; gap: 0.3rem;">
                ${getIcon("check", "", 12)} Complete
              </button>
            </div>
          </div>
        `;
      }).join("");

      listContainer.querySelectorAll(".complete-followup-btn").forEach(btn => {
        btn.onclick = async () => {
          const id = btn.getAttribute("data-id");
          try {
            await API.put(`/activity/followups/${id}`, { status: "COMPLETED" });
            showToast("Next Move marked complete!");
            initDashboardListeners();
          } catch (err) {
            showToast(err.message, "danger");
          }
        };
      });
    }

  } catch (err) {
    showToast("Failed to load dashboard metrics.", "danger");
  }
}

async function loadProfileBanner() {
  try {
    const p = await api.get("/profile");
    const sub = document.getElementById("dash-profile-status-sub");
    if (sub) {
      if (p.completeness_score >= 80) {
        sub.innerHTML = `Profile Completeness: <strong style="color: var(--accent-color);">${p.completeness_score}%</strong> (High Match Eligibility)`;
      } else {
        sub.innerHTML = `Profile Completeness: <strong style="color: var(--warning-color);">${p.completeness_score}%</strong> • Missing: ${p.missing_items.slice(0, 2).join(", ")}`;
      }
    }

    // Load ATS Score from latest resume
    const resumes = await api.get("/resumes");
    const atsScoreEl = document.getElementById("kpi-ats-score");
    if (atsScoreEl) {
      if (resumes && resumes.length > 0) {
        const top = resumes[0];
        const score = top.ats_score || top.quality_score || 0;
        atsScoreEl.textContent = `${score}/100`;
      } else {
        atsScoreEl.textContent = `N/A`;
      }
    }
  } catch (e) {
    // Optional
  }
}

async function loadRecommendedPreview() {
  const container = document.getElementById("dash-recs-preview");
  if (!container) return;

  try {
    const recs = await api.get("/recommendations?filter_type=ALL");
    if (!recs || recs.length === 0) {
      container.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem; padding: 1rem; text-align: center; grid-column: 1 / -1;">No recommendations found yet. Update your profile skills to view matching job openings.</div>`;
      return;
    }

    container.innerHTML = recs.slice(0, 3).map(r => `
      <div style="background: var(--bg-secondary); border-radius: var(--radius-md); padding: 1rem; border-left: 3px solid var(--primary-color);">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.35rem;">
          <h4 style="font-size: 0.9rem; font-weight: 700; color: var(--text-primary); margin: 0;">${r.title}</h4>
          <span style="font-weight: 800; font-size: 0.85rem; color: var(--primary-color);">${Math.round(r.match_score)}%</span>
        </div>
        <div style="font-size: 0.775rem; color: var(--text-muted); margin-bottom: 0.5rem;">${r.company_name} • ${r.location || 'Flexible'}</div>
        <a href="#/recommendations" class="btn btn-outline" style="font-size: 0.7rem; padding: 0.2rem 0.5rem; width: 100%; text-align: center; justify-content: center; gap: 0.3rem;">
          View & Apply ${getIcon("arrow-right", "", 12)}
        </a>
      </div>
    `).join("");
  } catch (e) {
    container.innerHTML = `<div style="color: var(--text-muted); font-size: 0.8rem; padding: 1rem; text-align: center;">Visit Role Matches tab to explore openings.</div>`;
  }
}

function openLogHRInteractionModal() {
  const content = `
    <form id="hr-interaction-form" style="display: flex; flex-direction: column; gap: 1rem;">
      <div class="form-group">
        <label>Company Name *</label>
        <input type="text" id="hr-comp-name" required placeholder="e.g. Acme Software Tech" class="form-control" />
      </div>
      <div class="form-group">
        <label>HR Contact Person</label>
        <input type="text" id="hr-person-name" placeholder="e.g. Priya Sharma (HR Lead)" class="form-control" />
      </div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
        <div class="form-group">
          <label>Interaction Type</label>
          <select id="hr-type" class="form-control">
            <option value="CALL">Phone Call</option>
            <option value="EMAIL">Email</option>
            <option value="LINKEDIN">LinkedIn Message</option>
            <option value="INTERVIEW">Interview</option>
          </select>
        </div>
        <div class="form-group">
          <label>Outcome</label>
          <select id="hr-outcome" class="form-control">
            <option value="CONNECTED">Connected / Discussed</option>
            <option value="RESUME_REQUESTED">Resume Requested</option>
            <option value="INTERVIEW_SCHEDULED">Interview Scheduled</option>
            <option value="REQUIREMENT_CLOSED">Requirement Closed</option>
            <option value="NO_ANSWER">No Answer</option>
          </select>
        </div>
      </div>
      <div class="form-group">
        <label>Interaction Notes *</label>
        <textarea id="hr-notes" required class="form-control" rows="3" placeholder="Discussed role requirements and salary budget..."></textarea>
      </div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
        <div class="form-group">
          <label>Next Move Action</label>
          <input type="text" id="hr-next-move" placeholder="e.g. Follow up on interview outcome" class="form-control" />
        </div>
        <div class="form-group">
          <label>Due Date</label>
          <input type="datetime-local" id="hr-due-date" class="form-control" />
        </div>
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 0.5rem;">
        <button type="button" class="btn btn-outline close-modal-btn">Cancel</button>
        <button type="submit" class="btn btn-primary" style="gap: 0.4rem;">
          ${getIcon("check", "", 16)} Save Interaction
        </button>
      </div>
    </form>
  `;

  const { closeModal } = createModal("Log HR Interaction", content);

  document.getElementById("hr-interaction-form").onsubmit = async (e) => {
    e.preventDefault();
    const company_name = document.getElementById("hr-comp-name").value.trim();
    const hr_name = document.getElementById("hr-person-name").value.trim();
    const interaction_type = document.getElementById("hr-type").value;
    const outcome = document.getElementById("hr-outcome").value;
    const notes = document.getElementById("hr-notes").value.trim();
    const next_move = document.getElementById("hr-next-move").value.trim();
    const dueVal = document.getElementById("hr-due-date").value;
    const due_date = dueVal ? new Date(dueVal).toISOString() : null;

    try {
      await api.post("/interactions", {
        company_name, hr_name, interaction_type, outcome, notes, next_move, due_date
      });
      showToast("HR interaction recorded & Next Move updated!");
      closeModal();
      initDashboardListeners();
    } catch (err) {
      showToast(err.message || "Failed to log interaction.", "danger");
    }
  };
}
