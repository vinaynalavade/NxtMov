import { api } from "../api.js";
import { showToast, createModal, formatBadge } from "../components.js";

export function renderSubmissionsView(container) {
  container.innerHTML = `
    <div style="max-width: 1200px; margin: 0 auto;">
      <div class="view-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.25rem;">Candidate Submissions & Placements</h2>
          <p style="color: var(--text-secondary); font-size: 0.875rem;">Track candidate submissions sent to client HRs and record confirmed placements.</p>
        </div>
        <button id="record-placement-btn" class="btn btn-primary">🏆 Record Placement</button>
      </div>

      <div class="card" style="margin-bottom: 1.5rem;">
        <h3 style="font-size: 1.1rem; margin-bottom: 1rem;">Candidate Submissions Pipeline</h3>
        <div id="submissions-table-container" class="table-responsive">
          <p style="color: var(--text-muted);">Loading submissions...</p>
        </div>
      </div>

      <div class="card">
        <h3 style="font-size: 1.1rem; margin-bottom: 1rem;">Confirmed Consultancy Placements</h3>
        <div id="placements-table-container" class="table-responsive">
          <p style="color: var(--text-muted);">Loading placements...</p>
        </div>
      </div>
    </div>
  `;

  loadSubmissionsAndPlacements();

  document.getElementById("record-placement-btn")?.addEventListener("click", openRecordPlacementModal);
}

async function loadSubmissionsAndPlacements() {
  const subContainer = document.getElementById("submissions-table-container");
  const placeContainer = document.getElementById("placements-table-container");

  try {
    const [submissions, placements] = await Promise.all([
      api.get("/submissions"),
      api.get("/placements")
    ]);

    // Submissions List
    if (submissions.length === 0) {
      subContainer.innerHTML = `<p style="color: var(--text-muted);">No candidate submissions found.</p>`;
    } else {
      subContainer.innerHTML = `
        <table style="width: 100%; border-collapse: collapse; text-align: left;">
          <thead>
            <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-secondary); font-size: 0.85rem;">
              <th style="padding: 0.75rem;">CANDIDATE</th>
              <th style="padding: 0.75rem;">REQUIREMENT & CLIENT</th>
              <th style="padding: 0.75rem;">SUBMITTED BY</th>
              <th style="padding: 0.75rem;">STATUS</th>
              <th style="padding: 0.75rem; text-align: right;">ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            ${submissions.map(s => `
              <tr style="border-bottom: 1px solid var(--border-color); font-size: 0.9rem;">
                <td style="padding: 0.875rem; font-weight: 600;">${s.candidate_name}</td>
                <td style="padding: 0.875rem;">
                  <div>${s.job_title}</div>
                  <div style="font-size: 0.75rem; color: var(--text-muted);">${s.company_name}</div>
                </td>
                <td style="padding: 0.875rem; color: var(--text-secondary);">${s.submitted_by_name || 'Recruiter'}</td>
                <td style="padding: 0.875rem;">${formatBadge(s.status)}</td>
                <td style="padding: 0.875rem; text-align: right;">
                  <button class="btn btn-outline update-sub-btn" data-id="${s.id}" data-status="${s.status}" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">Update Stage</button>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;

      subContainer.querySelectorAll(".update-sub-btn").forEach(btn => {
        btn.addEventListener("click", (e) => openUpdateSubmissionModal(e.target.dataset.id, e.target.dataset.status));
      });
    }

    // Placements List
    if (placements.length === 0) {
      placeContainer.innerHTML = `<p style="color: var(--text-muted);">No confirmed placements recorded yet.</p>`;
    } else {
      placeContainer.innerHTML = `
        <table style="width: 100%; border-collapse: collapse; text-align: left;">
          <thead>
            <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-secondary); font-size: 0.85rem;">
              <th style="padding: 0.75rem;">PLACED CANDIDATE</th>
              <th style="padding: 0.75rem;">COMPANY & ROLE</th>
              <th style="padding: 0.75rem;">JOINING DATE</th>
              <th style="padding: 0.75rem;">OFFER SALARY</th>
              <th style="padding: 0.75rem;">STATUS</th>
            </tr>
          </thead>
          <tbody>
            ${placements.map(p => `
              <tr style="border-bottom: 1px solid var(--border-color); font-size: 0.9rem;">
                <td style="padding: 0.875rem; font-weight: 600;">${p.candidate_name}</td>
                <td style="padding: 0.875rem;">
                  <div>${p.company_name}</div>
                  <div style="font-size: 0.75rem; color: var(--text-muted);">${p.job_title}</div>
                </td>
                <td style="padding: 0.875rem; color: var(--text-secondary);">${new Date(p.join_date).toLocaleDateString()}</td>
                <td style="padding: 0.875rem; font-weight: 500; color: var(--success-color);">${p.offered_salary ? '₹' + Number(p.offered_salary).toLocaleString() : '—'}</td>
                <td style="padding: 0.875rem;">${formatBadge(p.status)}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    }

  } catch (err) {
    showToast("Failed to load submissions and placements.", "error");
  }
}

function openUpdateSubmissionModal(subId, currentStatus) {
  const content = `
    <form id="update-sub-form" style="display: flex; flex-direction: column; gap: 1rem;">
      <div class="form-group">
        <label>Submission Stage *</label>
        <select id="sub-stage-select" class="form-control" required>
          <option value="SUBMITTED" ${currentStatus === 'SUBMITTED' ? 'selected' : ''}>SUBMITTED</option>
          <option value="SHORTLISTED" ${currentStatus === 'SHORTLISTED' ? 'selected' : ''}>SHORTLISTED</option>
          <option value="CLIENT_REVIEW" ${currentStatus === 'CLIENT_REVIEW' ? 'selected' : ''}>CLIENT_REVIEW</option>
          <option value="INTERVIEW" ${currentStatus === 'INTERVIEW' ? 'selected' : ''}>INTERVIEW</option>
          <option value="OFFER" ${currentStatus === 'OFFER' ? 'selected' : ''}>OFFER</option>
          <option value="PLACED" ${currentStatus === 'PLACED' ? 'selected' : ''}>PLACED</option>
          <option value="REJECTED" ${currentStatus === 'REJECTED' ? 'selected' : ''}>REJECTED</option>
        </select>
      </div>
      <div class="form-group">
        <label>Client HR Feedback</label>
        <textarea id="sub-feedback" rows="3" class="form-control" placeholder="HR comments, screening feedback..."></textarea>
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1rem;">
        <button type="button" class="btn btn-outline close-modal-btn">Cancel</button>
        <button type="submit" class="btn btn-primary">Update Submission</button>
      </div>
    </form>
  `;

  const { closeModal } = createModal("Update Candidate Submission Stage", content);

  document.getElementById("update-sub-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const status = document.getElementById("sub-stage-select").value;
    const client_feedback = document.getElementById("sub-feedback").value.trim();

    try {
      await api.put(`/submissions/${subId}`, { status, client_feedback });
      showToast("Submission updated!");
      closeModal();
      loadSubmissionsAndPlacements();
    } catch (err) {
      showToast(err.message || "Failed to update submission.", "error");
    }
  });
}

async function openRecordPlacementModal() {
  try {
    const [candidates, companies, requirements] = await Promise.all([
      api.get("/candidates?limit=100"),
      api.get("/companies"),
      api.get("/requirements")
    ]);

    const content = `
      <form id="record-placement-form" style="display: flex; flex-direction: column; gap: 1rem;">
        <div class="form-group">
          <label>Placed Candidate *</label>
          <select id="place-cand" class="form-control" required>
            <option value="">Select Candidate...</option>
            ${candidates.map(c => `<option value="${c.id}">${c.full_name} (${c.email})</option>`).join("")}
          </select>
        </div>

        <div class="form-group">
          <label>Hiring Company *</label>
          <select id="place-comp" class="form-control" required>
            <option value="">Select Company...</option>
            ${companies.map(c => `<option value="${c.id}">${c.name}</option>`).join("")}
          </select>
        </div>

        <div class="form-group">
          <label>Job Requirement / Opening *</label>
          <select id="place-req" class="form-control" required>
            <option value="">Select Requirement...</option>
            ${requirements.map(r => `<option value="${r.id}">${r.title} (${r.location})</option>`).join("")}
          </select>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
          <div class="form-group">
            <label>Joining Date *</label>
            <input type="date" id="place-date" required class="form-control" />
          </div>
          <div class="form-group">
            <label>Offered Salary (Annual ₹)</label>
            <input type="number" id="place-salary" placeholder="1800000" class="form-control" />
          </div>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1rem;">
          <button type="button" class="btn btn-outline close-modal-btn">Cancel</button>
          <button type="submit" class="btn btn-primary">Save Placement</button>
        </div>
      </form>
    `;

    const { closeModal } = createModal("Record Confirmed Consultancy Placement", content);

    document.getElementById("record-placement-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const candId = document.getElementById("place-cand").value;
      const compId = document.getElementById("place-comp").value;
      const reqId = document.getElementById("place-req").value;
      const join_date = document.getElementById("place-date").value;
      const salary = document.getElementById("place-salary").value;

      try {
        await api.post("/placements", {
          candidate_id: parseInt(candId),
          company_id: parseInt(compId),
          job_requirement_id: parseInt(reqId),
          join_date,
          offered_salary: salary ? parseFloat(salary) : null
        });
        showToast("Placement recorded successfully!");
        closeModal();
        loadSubmissionsAndPlacements();
      } catch (err) {
        showToast(err.message || "Failed to record placement.", "error");
      }
    });

  } catch (err) {
    showToast("Failed to load options for placement.", "error");
  }
}
