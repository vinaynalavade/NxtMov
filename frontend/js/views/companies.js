import { API } from "../api.js";
import { showToast, openModal } from "../components.js";

export function renderCompanies() {
  return `
    <div class="view-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
      <div>
        <h1 style="font-size: 1.5rem; font-weight: 700;">Employer Companies</h1>
        <p style="color: var(--text-secondary); font-size: 0.875rem;">Manage target employers and client organizations.</p>
      </div>
      <button id="add-company-btn" class="btn btn-primary">+ Add Company</button>
    </div>

    <div class="card" style="margin-bottom: 1.5rem; padding: 1rem;">
      <input type="text" id="company-search" class="form-input" placeholder="🔍 Search companies by name, industry, location..." style="width: 100%;">
    </div>

    <div class="card">
      <div id="companies-table-container">
        <p style="color: var(--text-muted); text-align: center; padding: 2rem;">Loading companies...</p>
      </div>
    </div>
  `;
}

export async function initCompaniesListeners() {
  const addBtn = document.getElementById("add-company-btn");
  const searchInput = document.getElementById("company-search");

  if (addBtn) {
    addBtn.onclick = () => openAddCompanyModal();
  }

  if (searchInput) {
    let timeout = null;
    searchInput.oninput = () => {
      clearTimeout(timeout);
      timeout = setTimeout(() => loadCompanies(searchInput.value.trim()), 300);
    };
  }

  loadCompanies();
}

async function loadCompanies(search = "") {
  try {
    const companies = await API.get(`/companies${search ? `?search=${encodeURIComponent(search)}` : ''}`);
    const container = document.getElementById("companies-table-container");

    if (!companies || companies.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 3rem 0; color: var(--text-secondary);">
          <p style="font-size: 1rem; font-weight: 500;">No companies found.</p>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem;">Click "+ Add Company" or import an Excel spreadsheet to get started.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="table-responsive">
        <table style="width: 100%; border-collapse: collapse; text-align: left;">
          <thead>
            <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-secondary); font-size: 0.85rem;">
              <th style="padding: 0.75rem;">COMPANY NAME</th>
              <th style="padding: 0.75rem;">INDUSTRY</th>
              <th style="padding: 0.75rem;">LOCATION</th>
              <th style="padding: 0.75rem;">WEBSITE</th>
              <th style="padding: 0.75rem; text-align: right;">ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            ${companies.map(c => `
              <tr style="border-bottom: 1px solid var(--border-color); font-size: 0.9rem;">
                <td style="padding: 0.875rem; font-weight: 600;">${c.name}</td>
                <td style="padding: 0.875rem; color: var(--text-secondary);">${c.industry || '—'}</td>
                <td style="padding: 0.875rem; color: var(--text-secondary);">${c.location || '—'}</td>
                <td style="padding: 0.875rem;">
                  ${c.website ? `<a href="${c.website.startsWith('http') ? c.website : 'https://' + c.website}" target="_blank" style="color: var(--primary-color); text-decoration: none;">${c.website}</a>` : '—'}
                </td>
                <td style="padding: 0.875rem; text-align: right;">
                  <button class="btn btn-outline view-contacts-btn" data-id="${c.id}" data-name="${c.name}" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">Contacts</button>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;

    container.querySelectorAll(".view-contacts-btn").forEach(btn => {
      btn.onclick = () => {
        const id = btn.getAttribute("data-id");
        window.location.hash = `#/contacts?company_id=${id}`;
      };
    });

  } catch (err) {
    showToast(err.message, "danger");
  }
}

function openAddCompanyModal() {
  const content = `
    <form id="company-modal-form">
      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 500; margin-bottom: 0.35rem;">Company Name *</label>
        <input type="text" id="modal-company-name" required placeholder="e.g. Infosys, TCS, Google" class="form-input" style="width: 100%;">
      </div>
      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 500; margin-bottom: 0.35rem;">Industry</label>
        <input type="text" id="modal-company-industry" placeholder="IT Services, Software, Finance" class="form-input" style="width: 100%;">
      </div>
      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 500; margin-bottom: 0.35rem;">Location</label>
        <input type="text" id="modal-company-location" placeholder="Bengaluru, Hyderabad, Remote" class="form-input" style="width: 100%;">
      </div>
      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 500; margin-bottom: 0.35rem;">Website</label>
        <input type="text" id="modal-company-website" placeholder="https://company.com" class="form-input" style="width: 100%;">
      </div>
      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 500; margin-bottom: 0.35rem;">Notes</label>
        <textarea id="modal-company-notes" rows="3" placeholder="Key details, company size, referral info..." class="form-input" style="width: 100%;"></textarea>
      </div>
    </form>
  `;

  openModal("Add Employer Company", content, async (close) => {
    const name = document.getElementById("modal-company-name").value.trim();
    if (!name) {
      showToast("Company name is required.", "danger");
      return;
    }
    const industry = document.getElementById("modal-company-industry").value.trim();
    const location = document.getElementById("modal-company-location").value.trim();
    const website = document.getElementById("modal-company-website").value.trim();
    const notes = document.getElementById("modal-company-notes").value.trim();

    try {
      await API.post("/companies", { name, industry, location, website, notes });
      showToast("Company added successfully!");
      close();
      loadCompanies();
    } catch (err) {
      showToast(err.message, "danger");
    }
  });
}
