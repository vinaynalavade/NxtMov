import { api, API } from "../api.js";
import { store } from "../store.js";
import { showToast, createModal } from "../components.js";
import { openContactDetailDrawer } from "./contacts.js";

export function renderDashboard() {
  const user = store.getState().user || { full_name: "User" };
  const firstName = user.full_name ? user.full_name.split(' ')[0] : 'User';

  return `
    <div class="dashboard-container">
      <div class="dashboard-header" style="margin-bottom: 1.5rem;">
        <h1 class="view-title">Good day, ${firstName}! 👋</h1>
        <p class="view-subtitle">Welcome to your recruitment & job-seeking control center. Explore role recommendations, manage applications, and record HR interactions.</p>
      </div>

      <!-- Profile Completeness & Quick Status Banner -->
      <div id="dash-profile-banner" class="card" style="margin-bottom: 1.5rem; background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
          <div>
            <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.2rem;">Talent Profile Status</h3>
            <p id="dash-profile-status-sub" style="font-size: 0.8rem; color: var(--text-muted);">Loading completeness...</p>
          </div>
          <div style="display: flex; gap: 0.75rem; align-items: center;">
            <a href="#/profile" class="btn btn-outline" style="font-size: 0.8rem;">👤 Edit Profile</a>
            <a href="#/resume" class="btn btn-primary" style="font-size: 0.8rem;">📄 Upload / Check Resume</a>
          </div>
        </div>
      </div>

      <!-- KPI Grid Cards -->
      <div class="kpi-grid" style="margin-bottom: 1.5rem;">
        <div class="card kpi-card">
          <div class="kpi-title">Follow-ups Due Today</div>
          <div id="kpi-today" class="kpi-value" style="color: var(--warning-color);">-</div>
          <div class="kpi-caption">Actions scheduled for today</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-title">Overdue Next Moves</div>
          <div id="kpi-overdue" class="kpi-value" style="color: var(--danger-color);">-</div>
          <div class="kpi-caption">Immediate attention needed</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-title">Active Opportunities</div>
          <div id="kpi-opportunities" class="kpi-value" style="color: var(--primary-color);">-</div>
          <div class="kpi-caption">Matched job openings</div>
        </div>

        <div class="card kpi-card">
          <div class="kpi-title">Applications & Interviews</div>
          <div id="kpi-applications" class="kpi-value" style="color: var(--accent-color);">-</div>
          <div class="kpi-caption">Submitted applications</div>
        </div>
      </div>

      <!-- Recommended Jobs Preview -->
      <div class="card" style="margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary);">🎯 Recommended Roles For You</h3>
          <a href="#/recommendations" class="btn btn-outline" style="font-size: 0.75rem;">View All Recommendations →</a>
        </div>
        <div id="dash-recs-preview" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem;">
          <div style="color: var(--text-muted); font-size: 0.85rem; padding: 1.5rem; text-align: center; grid-column: 1 / -1;">Loading recommendations...</div>
        </div>
      </div>

      <!-- Next Moves Engine & Quick Actions -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem; align-items: start;">
        <div class="card">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
            <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary);">⚡ YOUR NEXT MOVES (ACTION ENGINE)</h3>
            <a href="#/followups" class="btn btn-outline" style="font-size: 0.75rem;">View All</a>
          </div>
          <div id="dashboard-followups-list">
            <p style="color: var(--text-muted); font-size: 0.85rem; text-align: center; padding: 1.5rem 0;">Loading action items...</p>
          </div>
        </div>

        <div class="card">
          <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); margin-bottom: 1rem;">🚀 QUICK ACTIONS</h3>
          <div style="display: flex; flex-direction: column; gap: 0.65rem;">
            <button id="btn-quick-log-hr" class="btn btn-primary" style="justify-content: start;">📞 Log HR Interaction</button>
            <a href="#/profile" class="btn btn-outline" style="justify-content: start;">👤 My Profile & Settings</a>
            <a href="#/resume" class="btn btn-outline" style="justify-content: start;">📄 Resume Quality Analyzer</a>
            <a href="#/recommendations" class="btn btn-outline" style="justify-content: start;">🎯 Role Matching Engine</a>
            <a href="#/opportunities" class="btn btn-outline" style="justify-content: start;">💼 Job Requirements</a>
          </div>
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

  try {
    const stats = await API.get("/activity/dashboard/stats");

    const kpiToday = document.getElementById("kpi-today");
    const kpiOverdue = document.getElementById("kpi-overdue");
    const kpiOpps = document.getElementById("kpi-opportunities");
    const kpiApps = document.getElementById("kpi-applications");

    if (kpiToday) kpiToday.textContent = stats.followups_due_today;
    if (kpiOverdue) kpiOverdue.textContent = stats.overdue_followups;
    if (kpiOpps) kpiOpps.textContent = stats.active_opportunities;
    if (kpiApps) kpiApps.textContent = `${stats.applications_count} (${stats.interviews_count} Interviews)`;

    const listContainer = document.getElementById("dashboard-followups-list");
    if (!stats.today_followups || stats.today_followups.length === 0) {
      if (listContainer) {
        listContainer.innerHTML = `
          <div class="empty-state" style="margin: 0.5rem 0; padding: 1.5rem 1rem; text-align: center;">
            <span class="empty-state-icon" style="font-size: 1.8rem;">🎉</span>
            <div class="empty-state-title" style="font-weight: 700; margin-top: 0.25rem;">No pending follow-ups due today!</div>
            <div class="empty-state-description" style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.75rem;">Log HR calls or record responses to schedule your next move.</div>
            <button id="btn-dash-log-hr" class="btn btn-primary" style="font-size: 0.8rem;">📞 Log HR Interaction</button>
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
              <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.15rem;">
                📅 ${new Date(item.due_date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
              </div>
            </div>

            <div style="display: flex; gap: 0.4rem; align-items: center;">
              <button class="btn btn-primary complete-followup-btn" data-id="${item.id}" style="font-size: 0.75rem; padding: 0.25rem 0.6rem;">
                ✓ Complete
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
        <a href="#/recommendations" class="btn btn-outline" style="font-size: 0.7rem; padding: 0.2rem 0.5rem; width: 100%; text-align: center;">View & Apply</a>
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
        <button type="submit" class="btn btn-primary">Save Interaction</button>
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
