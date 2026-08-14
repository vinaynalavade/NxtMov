import { API } from "../api.js";
import { showToast, openModal, formatBadge } from "../components.js";
import { openContactDetailDrawer } from "./contacts.js";

export function renderOpportunities() {
  return `
    <div class="view-header">
      <div>
        <h1 class="view-title">Job Opportunities & Requisitions</h1>
        <p class="view-subtitle">Track target job openings, requirements, and linked HR contacts.</p>
      </div>
      <button id="add-opportunity-btn" class="btn btn-primary">+ Add Opportunity</button>
    </div>

    <div class="card" style="margin-bottom: 1.5rem; padding: 1rem;">
      <input type="text" id="opp-search" class="form-input" placeholder="🔍 Search opportunities by job title, skills, location..." style="width: 100%;">
    </div>

    <div class="card">
      <div id="opportunities-table-container">
        <p style="color: var(--text-muted); text-align: center; padding: 2rem;">Loading job opportunities...</p>
      </div>
    </div>
  `;
}

export async function initOpportunitiesListeners() {
  const addBtn = document.getElementById("add-opportunity-btn");
  const searchInput = document.getElementById("opp-search");

  if (addBtn) addBtn.onclick = () => openAddOpportunityModal();

  if (searchInput) {
    let timeout = null;
    searchInput.oninput = () => {
      clearTimeout(timeout);
      timeout = setTimeout(() => loadOpportunities(searchInput.value.trim()), 300);
    };
  }

  loadOpportunities();
}

async function loadOpportunities(search = "") {
  try {
    const opportunities = await API.get(`/requirements${search ? `?search=${encodeURIComponent(search)}` : ''}`);
    const container = document.getElementById("opportunities-table-container");

    if (!opportunities || opportunities.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <span class="empty-state-icon">💼</span>
          <div class="empty-state-title">No job opportunities tracked yet</div>
          <div class="empty-state-description">Add open positions discovered during HR calls to track applications and interviews.</div>
          <button id="empty-opp-btn" class="btn btn-primary">+ Add Opportunity</button>
        </div>
      `;
      const emptyBtn = document.getElementById("empty-opp-btn");
      if (emptyBtn) emptyBtn.onclick = () => openAddOpportunityModal();
      return;
    }

    container.innerHTML = `
      <div class="table-responsive">
        <table>
          <thead>
            <tr>
              <th>ROLE TITLE</th>
              <th>COMPANY & HR CONTACT</th>
              <th>LOCATION & TYPE</th>
              <th>STATUS</th>
              <th style="text-align: right;">ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            ${opportunities.map(o => `
              <tr>
                <td>
                  <div style="font-weight: 700; color: var(--text-primary);">${o.title}</div>
                  <div style="font-size: 0.75rem; color: var(--text-muted);">${o.skills_req || 'No specific skills listed'}</div>
                </td>
                <td>
                  <div style="font-weight: 600; color: var(--text-secondary);">${o.company ? o.company.name : '—'}</div>
                  ${o.contact ? `
                    <div style="font-size: 0.775rem; color: var(--primary-color); cursor: pointer;" class="view-contact-link" data-id="${o.contact.id}">
                      👤 ${o.contact.name} (${o.contact.designation || 'HR'})
                    </div>
                  ` : '<div style="font-size: 0.75rem; color: var(--text-muted);">No contact linked</div>'}
                </td>
                <td>
                  <div>${o.location || 'Remote'}</div>
                  <div style="font-size: 0.75rem; color: var(--text-muted);">${o.employment_type}</div>
                </td>
                <td>${formatBadge(o.status)}</td>
                <td style="text-align: right;">
                  <div style="display: flex; gap: 0.35rem; justify-content: flex-end;">
                    <button class="btn btn-primary apply-opportunity-btn" data-id="${o.id}" style="font-size: 0.75rem; padding: 0.25rem 0.6rem;">🚀 Apply Role</button>
                  </div>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;

    container.querySelectorAll(".view-contact-link").forEach(link => {
      link.onclick = () => {
        const contactId = link.getAttribute("data-id");
        openContactDetailDrawer(contactId);
      };
    });

    container.querySelectorAll(".apply-opportunity-btn").forEach(btn => {
      btn.onclick = async () => {
        const id = btn.getAttribute("data-id");
        try {
          await API.post("/applications", { job_requirement_id: parseInt(id, 10), stage: "APPLIED" });
          showToast("Application created & moving to tracking!");
          window.location.hash = "#/applications";
        } catch (err) {
          showToast(err.message, "danger");
        }
      };
    });

  } catch (err) {
    showToast(err.message, "danger");
  }
}

async function openAddOpportunityModal() {
  let companies = [];
  let contacts = [];
  try {
    companies = await API.get("/companies");
    contacts = await API.get("/contacts");
  } catch (e) {}

  if (!companies || companies.length === 0) {
    showToast("Please create at least one company first before adding an opportunity.", "warning");
    window.location.hash = "#/companies";
    return;
  }

  const content = `
    <form id="opportunity-modal-form">
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Company *</label>
          <select id="modal-opp-company" class="form-input" style="width: 100%;">
            ${companies.map(c => `<option value="${c.id}">${c.name}</option>`).join("")}
          </select>
        </div>
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Linked HR Contact</label>
          <select id="modal-opp-contact" class="form-input" style="width: 100%;">
            <option value="">-- Optional HR Contact --</option>
            ${contacts.map(c => `<option value="${c.id}">${c.name} (${c.company ? c.company.name : ''})</option>`).join("")}
          </select>
        </div>
      </div>

      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Job Role Title *</label>
        <input type="text" id="modal-opp-title" required placeholder="e.g. Senior QA Automation Engineer" class="form-input" style="width: 100%;">
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Location</label>
          <input type="text" id="modal-opp-location" placeholder="Bengaluru / Remote" class="form-input" style="width: 100%;">
        </div>
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Employment Type</label>
          <select id="modal-opp-type" class="form-input" style="width: 100%;">
            <option value="FULL_TIME">Full Time</option>
            <option value="CONTRACT">Contract</option>
            <option value="INTERNSHIP">Internship</option>
          </select>
        </div>
      </div>

      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Required Skills</label>
        <input type="text" id="modal-opp-skills" placeholder="Python, Selenium, Pytest, FastAPI" class="form-input" style="width: 100%;">
      </div>

      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Description / Notes</label>
        <textarea id="modal-opp-desc" rows="3" placeholder="Job description and requirement notes..." class="form-input" style="width: 100%;"></textarea>
      </div>
    </form>
  `;

  openModal("Add Job Opportunity", content, async (close) => {
    const company_id = parseInt(document.getElementById("modal-opp-company").value, 10);
    const contactIdVal = document.getElementById("modal-opp-contact").value;
    const contact_id = contactIdVal ? parseInt(contactIdVal, 10) : null;
    const title = document.getElementById("modal-opp-title").value.trim();

    if (!title) {
      showToast("Job title is required.", "danger");
      return;
    }
    const location = document.getElementById("modal-opp-location").value.trim();
    const employment_type = document.getElementById("modal-opp-type").value;
    const skills_req = document.getElementById("modal-opp-skills").value.trim();
    const description = document.getElementById("modal-opp-desc").value.trim();

    try {
      await API.post("/requirements", { company_id, contact_id, title, location, employment_type, skills_req, description });
      showToast("Job Opportunity added!");
      close();
      loadOpportunities();
    } catch (err) {
      showToast(err.message, "danger");
    }
  });
}
