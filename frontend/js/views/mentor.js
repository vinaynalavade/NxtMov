import { api } from "../api.js";
import { showToast, openDrawer } from "../components.js";

export function renderMentorView() {
  return `
    <div class="view-header">
      <div>
        <h1 class="view-title">🎓 Mentor Dashboard & Student Guidance Ecosystem</h1>
        <p class="view-subtitle">Track assigned students, monitor profile completeness, inspect recruitment journeys, and intervene on attention flags.</p>
      </div>
    </div>

    <!-- Summary KPI Cards -->
    <div id="mentor-kpi-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
      <div class="card" style="padding: 1rem;">
        <div style="font-size: 0.75rem; color: var(--text-muted);">TOTAL STUDENTS</div>
        <div id="kpi-total-students" style="font-size: 1.5rem; font-weight: 700; color: var(--primary-color); margin-top: 0.2rem;">-</div>
      </div>
      <div class="card" style="padding: 1rem;">
        <div style="font-size: 0.75rem; color: var(--text-muted);">MISSING RESUME</div>
        <div id="kpi-missing-resume" style="font-size: 1.5rem; font-weight: 700; color: var(--danger-color); margin-top: 0.2rem;">-</div>
      </div>
      <div class="card" style="padding: 1rem;">
        <div style="font-size: 0.75rem; color: var(--text-muted);">INCOMPLETE PROFILE</div>
        <div id="kpi-incomplete-profile" style="font-size: 1.5rem; font-weight: 700; color: var(--warning-color); margin-top: 0.2rem;">-</div>
      </div>
      <div class="card" style="padding: 1rem;">
        <div style="font-size: 0.75rem; color: var(--text-muted);">INTERVIEWS SCHEDULED</div>
        <div id="kpi-interviews-scheduled" style="font-size: 1.5rem; font-weight: 700; color: var(--accent-color); margin-top: 0.2rem;">-</div>
      </div>
    </div>

    <!-- Student Table Card -->
    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.75rem;">
        <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary);">Assigned Students Roster</h3>
        <input type="text" id="student-search-input" class="form-control" placeholder="Search by name, email, or skill..." style="max-width: 280px; font-size: 0.85rem;" />
      </div>

      <div id="students-table-container">
        <div style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading students roster...</div>
      </div>
    </div>
  `;
}

export function initMentorListeners() {
  loadMentorData();

  const searchInput = document.getElementById("student-search-input");
  if (searchInput) {
    searchInput.oninput = () => {
      filterStudentsTable(searchInput.value.trim().toLowerCase());
    };
  }
}

let cachedStudentsData = [];

async function loadMentorData() {
  try {
    const res = await api.get("/mentor/students");
    cachedStudentsData = res.students || [];

    document.getElementById("kpi-total-students").textContent = res.total_students || 0;
    document.getElementById("kpi-missing-resume").textContent = res.summary.missing_resume || 0;
    document.getElementById("kpi-incomplete-profile").textContent = res.summary.incomplete_profile || 0;
    document.getElementById("kpi-interviews-scheduled").textContent = res.summary.interviews_scheduled || 0;

    renderStudentsTable(cachedStudentsData);

  } catch (err) {
    showToast(err.message || "Failed to load mentor dashboard.", "danger");
  }
}

function filterStudentsTable(query) {
  if (!query) {
    renderStudentsTable(cachedStudentsData);
    return;
  }
  const filtered = cachedStudentsData.filter(s =>
    s.full_name.toLowerCase().includes(query) ||
    s.email.toLowerCase().includes(query) ||
    (s.location && s.location.toLowerCase().includes(query))
  );
  renderStudentsTable(filtered);
}

function renderStudentsTable(students) {
  const container = document.getElementById("students-table-container");
  if (!container) return;

  if (!students || students.length === 0) {
    container.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--text-muted);">No student candidates match your filter.</div>`;
    return;
  }

  container.innerHTML = `
    <div class="table-responsive">
      <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
        <thead>
          <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-secondary); text-align: left;">
            <th style="padding: 0.6rem;">STUDENT NAME</th>
            <th style="padding: 0.6rem;">CONTACT & LOCATION</th>
            <th style="padding: 0.6rem;">PROFILE SCORE</th>
            <th style="padding: 0.6rem;">ACTIVITY METRICS</th>
            <th style="padding: 0.6rem;">ATTENTION FLAGS</th>
            <th style="padding: 0.6rem; text-align: right;">ACTION</th>
          </tr>
        </thead>
        <tbody>
          ${students.map(s => `
            <tr style="border-bottom: 1px solid var(--border-color);">
              <td style="padding: 0.6rem;">
                <div style="font-weight: 700; color: var(--text-primary);">${s.full_name}</div>
                <span class="badge-status badge-info" style="font-size: 0.65rem;">${s.status}</span>
              </td>
              <td style="padding: 0.6rem;">
                <div>${s.email}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">${s.phone || '—'} | ${s.location || 'Location flexible'}</div>
              </td>
              <td style="padding: 0.6rem;">
                <div style="font-weight: 700; color: ${s.completeness_score >= 80 ? 'var(--accent-color)' : 'var(--warning-color)'};">${s.completeness_score}%</div>
                <div style="width: 80px; height: 6px; background-color: var(--border-color); border-radius: 999px; overflow: hidden; margin-top: 0.2rem;">
                  <div style="width: ${s.completeness_score}%; height: 100%; background-color: ${s.completeness_score >= 80 ? 'var(--accent-color)' : 'var(--warning-color)'};"></div>
                </div>
              </td>
              <td style="padding: 0.6rem;">
                <div style="font-size: 0.775rem;">
                  📄 Resumes: ${s.resumes_count} | 🎯 Apps: ${s.applications_count} | 📞 Calls: ${s.interactions_count}
                </div>
              </td>
              <td style="padding: 0.6rem;">
                ${s.requires_attention ? s.attention_reasons.map(r => `<span class="badge-status badge-danger" style="font-size: 0.65rem; margin-right: 0.2rem;">⚠️ ${r}</span>`).join("") : '<span class="badge-status badge-success" style="font-size: 0.65rem;">✓ On Track</span>'}
              </td>
              <td style="padding: 0.6rem; text-align: right;">
                <button class="btn btn-outline view-journey-btn" data-id="${s.id}" style="font-size: 0.75rem; padding: 0.3rem 0.6rem;">🗺️ View Journey</button>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;

  container.querySelectorAll(".view-journey-btn").forEach(btn => {
    btn.onclick = async () => {
      const id = btn.getAttribute("data-id");
      await openStudentJourneyDrawer(id);
    };
  });
}

async function openStudentJourneyDrawer(studentId) {
  try {
    showToast("Loading student journey timeline...", "info");
    const j = await api.get(`/mentor/students/${studentId}/journey`);

    const html = `
      <div style="margin-bottom: 1.5rem; background: var(--bg-secondary); padding: 1rem; border-radius: var(--radius-md);">
        <div style="font-weight: 700; font-size: 1rem; color: var(--text-primary);">${j.full_name}</div>
        <div style="font-size: 0.8rem; color: var(--text-muted);">${j.email} • Profile Completeness: ${j.completeness_score}%</div>
      </div>

      <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary); margin-bottom: 1rem;">Unified Recruitment Timeline</h4>

      ${!j.timeline || j.timeline.length === 0 ? `
        <div style="color: var(--text-muted); font-size: 0.85rem; padding: 1.5rem; text-align: center;">No recruitment events recorded yet for this student.</div>
      ` : `
        <div style="display: flex; flex-direction: column; gap: 1rem; position: relative; padding-left: 1.25rem; border-left: 2px solid var(--border-color);">
          ${j.timeline.map(t => `
            <div style="position: relative;">
              <div style="position: absolute; left: -1.65rem; top: 0.2rem; width: 10px; height: 10px; border-radius: 50%; background-color: var(--primary-color);"></div>
              <div style="font-size: 0.725rem; color: var(--text-muted);">${t.timestamp ? new Date(t.timestamp).toLocaleString() : 'Recent'}</div>
              <div style="font-weight: 700; font-size: 0.875rem; color: var(--text-primary); margin-top: 0.1rem;">${t.title}</div>
              <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.15rem;">${t.detail}</div>
            </div>
          `).join("")}
        </div>
      `}
    `;

    openDrawer(`Recruitment Journey: ${j.full_name}`, html);

  } catch (err) {
    showToast("Failed to load student journey.", "danger");
  }
}
