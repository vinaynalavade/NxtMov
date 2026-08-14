import { api } from "../api.js";
import { showToast, createModal, formatBadge } from "../components.js";

export function renderCandidatesView(container) {
  container.innerHTML = `
    <div style="max-width: 1200px; margin: 0 auto;">
      <div class="view-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.25rem;">Candidate Pool</h2>
          <p style="color: var(--text-secondary); font-size: 0.875rem;">Manage talent profiles, candidate matching, and submissions.</p>
        </div>
        <button id="add-candidate-btn" class="btn btn-primary">+ Add Candidate</button>
      </div>

      <!-- Filters Bar -->
      <div class="card" style="margin-bottom: 1.5rem; padding: 1rem;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
          <input type="text" id="cand-search-input" placeholder="Search candidate name, email, title..." class="form-control" />
          <input type="text" id="cand-skills-input" placeholder="Filter by skills (e.g. Python, React)..." class="form-control" />
          <select id="cand-status-filter" class="form-control">
            <option value="">All Statuses</option>
            <option value="NEW">New</option>
            <option value="SCREENING">Screening</option>
            <option value="READY">Ready</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="INTERVIEWING">Interviewing</option>
            <option value="OFFERED">Offered</option>
            <option value="PLACED">Placed</option>
          </select>
          <button id="cand-filter-btn" class="btn btn-outline">Filter</button>
        </div>
      </div>

      <div class="card">
        <div id="candidates-table-container" class="table-responsive">
          <p style="color: var(--text-muted);">Loading candidates...</p>
        </div>
      </div>
    </div>
  `;

  loadCandidates();

  document.getElementById("add-candidate-btn")?.addEventListener("click", openAddCandidateModal);
  document.getElementById("cand-filter-btn")?.addEventListener("click", loadCandidates);
}

async function loadCandidates() {
  const container = document.getElementById("candidates-table-container");
  const search = document.getElementById("cand-search-input")?.value.trim();
  const skills = document.getElementById("cand-skills-input")?.value.trim();
  const status = document.getElementById("cand-status-filter")?.value;

  let queryStr = "?limit=100";
  if (search) queryStr += `&search=${encodeURIComponent(search)}`;
  if (skills) queryStr += `&skills=${encodeURIComponent(skills)}`;
  if (status) queryStr += `&status=${encodeURIComponent(status)}`;

  try {
    const candidates = await api.get(`/candidates${queryStr}`);
    if (candidates.length === 0) {
      container.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No candidates found matching criteria.</p>`;
      return;
    }

    container.innerHTML = `
      <table style="width: 100%; border-collapse: collapse; text-align: left;">
        <thead>
          <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-secondary); font-size: 0.85rem;">
            <th style="padding: 0.75rem;">CANDIDATE NAME</th>
            <th style="padding: 0.75rem;">TITLE & COMPANY</th>
            <th style="padding: 0.75rem;">SKILLS & EXP</th>
            <th style="padding: 0.75rem;">STATUS</th>
            <th style="padding: 0.75rem; text-align: right;">ACTIONS</th>
          </tr>
        </thead>
        <tbody>
          ${candidates.map(c => `
            <tr style="border-bottom: 1px solid var(--border-color); font-size: 0.9rem;">
              <td style="padding: 0.875rem;">
                <div style="font-weight: 600; color: var(--primary-color); cursor: pointer;" class="cand-name-link" data-id="${c.id}">${c.full_name}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">${c.email} | ${c.phone || 'No Phone'}</div>
              </td>
              <td style="padding: 0.875rem;">
                <div>${c.current_title || 'Software Specialist'}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">${c.current_company || 'Independent'}</div>
              </td>
              <td style="padding: 0.875rem;">
                <div style="font-size: 0.85rem;">${c.primary_skills || c.skills || '—'}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">${c.experience_years ? c.experience_years + ' yrs exp' : 'Fresh Candidate'}</div>
              </td>
              <td style="padding: 0.875rem;">${formatBadge(c.status)}</td>
              <td style="padding: 0.875rem; text-align: right;">
                <button class="btn btn-outline match-cand-btn" data-id="${c.id}" data-name="${c.full_name}" style="font-size: 0.75rem; padding: 0.25rem 0.5rem; margin-right: 0.25rem;">🎯 Match Jobs</button>
                <button class="btn btn-primary view-cand-btn" data-id="${c.id}" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">Profile</button>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;

    container.querySelectorAll(".cand-name-link, .view-cand-btn").forEach(btn => {
      btn.addEventListener("click", (e) => openCandidateProfile(e.target.dataset.id));
    });

    container.querySelectorAll(".match-cand-btn").forEach(btn => {
      btn.addEventListener("click", (e) => openCandidateMatches(e.target.dataset.id, e.target.dataset.name));
    });

  } catch (err) {
    showToast("Failed to load candidates.", "error");
  }
}

async function openCandidateProfile(candId) {
  try {
    const profileData = await api.get(`/candidates/${candId}/profile`);
    const c = profileData.candidate;

    const content = `
      <div style="display: flex; flex-direction: column; gap: 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid var(--border-color); padding-bottom: 1rem;">
          <div>
            <h3 style="font-size: 1.25rem; font-weight: 700;">${c.full_name}</h3>
            <p style="color: var(--text-secondary); font-size: 0.875rem;">${c.current_title || 'Candidate'} @ ${c.current_company || 'Unassigned'}</p>
          </div>
          <div>${formatBadge(c.status)}</div>
        </div>

        <div style="grid-template-columns: 1fr 1fr; display: grid; gap: 1rem; font-size: 0.875rem;">
          <div><strong>Email:</strong> ${c.email}</div>
          <div><strong>Phone:</strong> ${c.phone || '—'}</div>
          <div><strong>Location:</strong> ${c.location || '—'}</div>
          <div><strong>Experience:</strong> ${c.experience_years ? c.experience_years + ' years' : '—'}</div>
          <div><strong>Notice Period:</strong> ${c.notice_period_days ? c.notice_period_days + ' days' : 'Immediate'}</div>
          <div><strong>Expected Salary:</strong> ${c.expected_salary ? '₹' + Number(c.expected_salary).toLocaleString() : '—'}</div>
          <div><strong>Counselor:</strong> ${c.counselor_name || 'Unassigned'}</div>
          <div><strong>Recruiter:</strong> ${c.recruiter_name || 'Unassigned'}</div>
        </div>

        <div style="background: var(--card-bg); padding: 0.75rem; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
          <strong style="font-size: 0.85rem; color: var(--text-secondary);">Primary Skills:</strong>
          <p style="font-size: 0.9rem; font-weight: 500; margin-top: 0.25rem;">${c.primary_skills || c.skills || 'No skills listed.'}</p>
        </div>

        <div>
          <h4 style="font-size: 1rem; margin-bottom: 0.5rem;">Submissions & Client Pipeline (${profileData.submissions_count})</h4>
          ${profileData.submissions.length === 0 ? `<p style="color: var(--text-muted); font-size: 0.85rem;">No active submissions for this candidate.</p>` : `
            <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.5rem;">
              ${profileData.submissions.map(s => `
                <li style="padding: 0.5rem; background: var(--bg-hover); border-radius: 4px; display: flex; justify-content: space-between; font-size: 0.85rem;">
                  <span><strong>${s.job_title}</strong> (${s.company_name})</span>
                  <span class="badge badge-info">${s.status}</span>
                </li>
              `).join("")}
            </ul>
          `}
        </div>

        <div style="display: flex; justify-content: flex-end; margin-top: 1rem;">
          <button class="btn btn-outline close-modal-btn">Close</button>
        </div>
      </div>
    `;

    createModal(`Candidate Profile 360`, content);
  } catch (err) {
    showToast("Failed to load candidate profile.", "error");
  }
}

async function openCandidateMatches(candId, candName) {
  try {
    const matches = await api.get(`/candidates/${candId}/matches`);
    const content = `
      <div style="display: flex; flex-direction: column; gap: 1rem; max-height: 70vh; overflow-y: auto;">
        <p style="color: var(--text-secondary); font-size: 0.875rem;">Showing top requirement matches for <strong>${candName}</strong> calculated by NxtMov Matching Engine.</p>
        ${matches.length === 0 ? `<p style="color: var(--text-muted);">No matching job requirements found.</p>` : `
          <div style="display: flex; flex-direction: column; gap: 1rem;">
            ${matches.map(m => `
              <div style="border: 1px solid var(--border-color); padding: 1rem; border-radius: var(--radius-md); background: var(--card-bg);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                  <div>
                    <h4 style="font-size: 1rem; font-weight: 700; color: var(--text-primary);">${m.job_title}</h4>
                    <span style="font-size: 0.75rem; color: var(--text-muted);">Req ID: #${m.job_requirement_id}</span>
                  </div>
                  <div style="text-align: right;">
                    <span style="font-size: 1.25rem; font-weight: 800; color: var(--primary-color);">${m.match_score}%</span>
                    <div style="font-size: 0.7rem; color: var(--text-secondary);">${m.score_label}</div>
                  </div>
                </div>

                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.75rem;">
                  ${m.pros.map(p => `<span style="background: rgba(16, 185, 129, 0.1); color: var(--success-color); font-size: 0.75rem; padding: 0.2rem 0.5rem; border-radius: 4px;">✓ ${p}</span>`).join("")}
                  ${m.gaps.map(g => `<span style="background: rgba(239, 68, 68, 0.1); color: var(--error-color); font-size: 0.75rem; padding: 0.2rem 0.5rem; border-radius: 4px;">⚠ ${g}</span>`).join("")}
                </div>

                <button class="btn btn-primary submit-cand-match-btn" data-req-id="${m.job_requirement_id}" data-cand-id="${candId}" style="font-size: 0.75rem; padding: 0.25rem 0.6rem;">Submit Candidate to Job</button>
              </div>
            `).join("")}
          </div>
        `}
      </div>
    `;

    const { closeModal } = createModal(`NxtMov Job Matches for ${candName}`, content);

    document.querySelectorAll(".submit-cand-match-btn").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        const reqId = e.target.dataset.reqId;
        const cId = e.target.dataset.candId;
        try {
          await api.post("/submissions", { job_requirement_id: parseInt(reqId), candidate_id: parseInt(cId) });
          showToast("Candidate submitted successfully!");
          closeModal();
        } catch (err) {
          showToast(err.message || "Failed to submit candidate.", "error");
        }
      });
    });

  } catch (err) {
    showToast("Failed to load candidate matches.", "error");
  }
}

function openAddCandidateModal() {
  const content = `
    <form id="add-cand-form" style="display: flex; flex-direction: column; gap: 1rem;">
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
        <div class="form-group">
          <label>Full Name *</label>
          <input type="text" id="cand-name" required placeholder="e.g. Rahul Patil" class="form-control" />
        </div>
        <div class="form-group">
          <label>Email Address *</label>
          <input type="email" id="cand-email" required placeholder="rahul@example.com" class="form-control" />
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
        <div class="form-group">
          <label>Phone Number</label>
          <input type="text" id="cand-phone" placeholder="+91 9876543210" class="form-control" />
        </div>
        <div class="form-group">
          <label>Location / City</label>
          <input type="text" id="cand-location" placeholder="Bengaluru" class="form-control" />
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
        <div class="form-group">
          <label>Primary Skills *</label>
          <input type="text" id="cand-skills" required placeholder="Python, Pytest, FastAPI, Docker" class="form-control" />
        </div>
        <div class="form-group">
          <label>Experience (Years)</label>
          <input type="number" step="0.5" id="cand-exp" placeholder="4.5" class="form-control" />
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
        <div class="form-group">
          <label>Current Company</label>
          <input type="text" id="cand-company" placeholder="TCS / Infosys" class="form-control" />
        </div>
        <div class="form-group">
          <label>Expected Salary (Annual ₹)</label>
          <input type="number" id="cand-expected-sal" placeholder="1800000" class="form-control" />
        </div>
      </div>

      <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1rem;">
        <button type="button" class="btn btn-outline close-modal-btn">Cancel</button>
        <button type="submit" class="btn btn-primary">Create Candidate</button>
      </div>
    </form>
  `;

  const { closeModal } = createModal("Add Candidate to Pool", content);

  document.getElementById("add-cand-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const full_name = document.getElementById("cand-name").value.trim();
    const email = document.getElementById("cand-email").value.trim();
    const phone = document.getElementById("cand-phone").value.trim();
    const location = document.getElementById("cand-location").value.trim();
    const primary_skills = document.getElementById("cand-skills").value.trim();
    const exp = document.getElementById("cand-exp").value;
    const current_company = document.getElementById("cand-company").value.trim();
    const expected_salary = document.getElementById("cand-expected-sal").value;

    try {
      await api.post("/candidates", {
        full_name,
        email,
        phone,
        location,
        primary_skills,
        experience_years: exp ? parseFloat(exp) : null,
        current_company,
        expected_salary: expected_salary ? parseFloat(expected_salary) : null
      });
      showToast("Candidate added successfully!");
      closeModal();
      loadCandidates();
    } catch (err) {
      showToast(err.message || "Failed to create candidate.", "error");
    }
  });
}
