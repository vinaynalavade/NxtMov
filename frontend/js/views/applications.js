import { API } from "../api.js";
import { showToast, openModal, formatBadge } from "../components.js";

export function renderApplications() {
  return `
    <div class="view-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
      <div>
        <h1 style="font-size: 1.5rem; font-weight: 700;">Applications & Interview Pipeline</h1>
        <p style="color: var(--text-secondary); font-size: 0.875rem;">Track application status, interview schedules, and job offer outcomes.</p>
      </div>
      <a href="#/opportunities" class="btn btn-primary">+ Apply New Opportunity</a>
    </div>

    <div class="card">
      <div id="applications-container">
        <p style="color: var(--text-muted); text-align: center; padding: 2rem;">Loading applications...</p>
      </div>
    </div>
  `;
}

export async function initApplicationsListeners() {
  loadApplications();
}

async function loadApplications() {
  try {
    const applications = await API.get("/applications");
    const container = document.getElementById("applications-container");

    if (!applications || applications.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 3rem 0; color: var(--text-secondary);">
          <p style="font-size: 1rem; font-weight: 500;">No active applications recorded.</p>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem;">Go to Opportunities to track your active job applications.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 1rem;">
        ${applications.map(app => `
          <div class="card" style="padding: 1.25rem; border-left: 4px solid var(--primary-color);">
            <div style="display: flex; justify-content: space-between; align-items: start;">
              <div>
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                  <h3 style="font-size: 1.1rem; font-weight: 700;">${app.job_requirement ? app.job_requirement.title : 'Application'}</h3>
                  ${formatBadge(app.stage)}
                </div>
                <div style="color: var(--text-secondary); font-size: 0.9rem; font-weight: 500; margin-top: 0.2rem;">
                  ${app.job_requirement && app.job_requirement.company ? app.job_requirement.company.name : 'Employer'}
                </div>
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.35rem;">
                  Applied on: ${new Date(app.applied_at).toLocaleDateString()}
                </div>
              </div>
              <div style="display: flex; gap: 0.5rem;">
                <select class="form-input update-stage-select" data-id="${app.id}" style="font-size: 0.8rem;">
                  <option value="APPLIED" ${app.stage === 'APPLIED' ? 'selected' : ''}>Applied</option>
                  <option value="SCREENING" ${app.stage === 'SCREENING' ? 'selected' : ''}>Screening</option>
                  <option value="INTERVIEWING" ${app.stage === 'INTERVIEWING' ? 'selected' : ''}>Interviewing</option>
                  <option value="OFFERED" ${app.stage === 'OFFERED' ? 'selected' : ''}>Offered</option>
                  <option value="REJECTED" ${app.stage === 'REJECTED' ? 'selected' : ''}>Rejected</option>
                </select>
                <button class="btn btn-primary schedule-interview-btn" data-id="${app.id}" style="font-size: 0.75rem; padding: 0.35rem 0.65rem;">+ Schedule Interview</button>
              </div>
            </div>

            <!-- Interviews list -->
            ${app.interviews && app.interviews.length > 0 ? `
              <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px dashed var(--border-color);">
                <div style="font-size: 0.8rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.5rem;">SCHEDULED INTERVIEW ROUNDS:</div>
                <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                  ${app.interviews.map(i => `
                    <div style="background: var(--bg-primary); padding: 0.5rem 0.75rem; border-radius: var(--radius-sm); font-size: 0.85rem; display: flex; justify-content: space-between;">
                      <div>
                        <strong>${i.round_name}</strong> — ${new Date(i.scheduled_at).toLocaleString()}
                        ${i.location_or_link ? `<div style="font-size: 0.75rem; color: var(--primary-color);">${i.location_or_link}</div>` : ''}
                      </div>
                      <span class="badge-status badge-info" style="font-size: 0.7rem;">${i.outcome}</span>
                    </div>
                  `).join("")}
                </div>
              </div>
            ` : ''}
          </div>
        `).join("")}
      </div>
    `;

    // Stage change listener
    container.querySelectorAll(".update-stage-select").forEach(sel => {
      sel.onchange = async () => {
        const id = sel.getAttribute("data-id");
        const newStage = sel.value;
        try {
          await API.put(`/applications/${id}`, { stage: newStage });
          showToast(`Application updated to ${newStage}`);
          loadApplications();
        } catch (err) {
          showToast(err.message, "danger");
        }
      };
    });

    // Schedule interview listener
    container.querySelectorAll(".schedule-interview-btn").forEach(btn => {
      btn.onclick = () => {
        const id = btn.getAttribute("data-id");
        openScheduleInterviewModal(id);
      };
    });

  } catch (err) {
    showToast(err.message, "danger");
  }
}

function openScheduleInterviewModal(applicationId) {
  const content = `
    <form id="interview-modal-form">
      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 500; margin-bottom: 0.35rem;">Interview Round Name *</label>
        <input type="text" id="modal-int-round" required placeholder="e.g. Technical Round 1, Managerial Round" class="form-input" style="width: 100%;">
      </div>

      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 500; margin-bottom: 0.35rem;">Date & Time *</label>
        <input type="datetime-local" id="modal-int-datetime" required class="form-input" style="width: 100%;">
      </div>

      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 500; margin-bottom: 0.35rem;">Meeting Link / Location</label>
        <input type="text" id="modal-int-link" placeholder="https://meet.google.com/abc-defg-hij" class="form-input" style="width: 100%;">
      </div>

      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 500; margin-bottom: 0.35rem;">Interviewer Names</label>
        <input type="text" id="modal-int-interviewers" placeholder="e.g. Rajesh Kumar (Tech Lead)" class="form-input" style="width: 100%;">
      </div>
    </form>
  `;

  openModal("Schedule Interview Round", content, async (close) => {
    const round_name = document.getElementById("modal-int-round").value.trim();
    const dt_val = document.getElementById("modal-int-datetime").value;
    if (!round_name || !dt_val) {
      showToast("Round name and Date/Time are required.", "danger");
      return;
    }

    const scheduled_at = new Date(dt_val).toISOString();
    const location_or_link = document.getElementById("modal-int-link").value.trim();
    const interviewer_names = document.getElementById("modal-int-interviewers").value.trim();

    try {
      await API.post(`/applications/${applicationId}/interviews`, {
        round_name,
        scheduled_at,
        location_or_link,
        interviewer_names
      });

      showToast("Interview scheduled!");
      close();
      loadApplications();
    } catch (err) {
      showToast(err.message, "danger");
    }
  });

  const datetimeInput = document.getElementById("modal-int-datetime");
  if (datetimeInput) {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(14, 0, 0, 0);
    datetimeInput.value = tomorrow.toISOString().slice(0, 16);
  }
}
