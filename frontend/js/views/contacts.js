import { API } from "../api.js";
import { showToast, openModal, openDrawer, formatBadge, formatRelativeTime } from "../components.js";

export function renderContacts() {
  return `
    <div class="view-header">
      <div>
        <h1 class="view-title">HR Contacts & Relationship Manager</h1>
        <p class="view-subtitle">Track HR personnel, recruiters, conversation history, and Next Move follow-ups.</p>
      </div>
      <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
        <a href="#/import" class="btn btn-outline">📊 Import Excel</a>
        <button id="add-contact-btn" class="btn btn-primary">+ Add HR Contact</button>
      </div>
    </div>

    <!-- Enhanced CRM Filter Bar -->
    <div class="crm-filter-bar">
      <input type="text" id="contact-search" class="form-input" placeholder="🔍 Search HR name, designation, company, phone..." style="flex: 2; min-width: 220px;">
      
      <select id="contact-status-filter" class="form-input" style="flex: 1; min-width: 150px;">
        <option value="">All Statuses</option>
        <option value="NOT_CONTACTED">Not Contacted</option>
        <option value="CONTACTED">Contacted</option>
        <option value="INTERESTED">Interested</option>
        <option value="KEEP_IN_TOUCH">Keep In Touch</option>
        <option value="OPPORTUNITY_AVAILABLE">Opportunity Available</option>
        <option value="NOT_RELEVANT">Not Relevant</option>
        <option value="DO_NOT_CONTACT">Do Not Contact</option>
      </select>

      <select id="contact-company-filter" class="form-input" style="flex: 1; min-width: 150px;">
        <option value="">All Companies</option>
      </select>

      <select id="contact-followup-filter" class="form-input" style="flex: 1; min-width: 150px;">
        <option value="">All Follow-ups</option>
        <option value="true">Has Next Move</option>
        <option value="false">No Next Move</option>
      </select>

      <button id="clear-filters-btn" class="btn btn-outline" style="padding: 0.625rem 0.875rem;">✖ Reset</button>
    </div>

    <div class="card">
      <div id="contacts-table-container">
        <p style="color: var(--text-muted); text-align: center; padding: 2rem;">Loading HR contacts...</p>
      </div>
    </div>
  `;
}

export async function initContactsListeners() {
  const addBtn = document.getElementById("add-contact-btn");
  const searchInput = document.getElementById("contact-search");
  const statusFilter = document.getElementById("contact-status-filter");
  const companyFilter = document.getElementById("contact-company-filter");
  const followupFilter = document.getElementById("contact-followup-filter");
  const clearFiltersBtn = document.getElementById("clear-filters-btn");

  if (addBtn) addBtn.onclick = () => openAddEditContactModal();

  // Populate company dropdown
  try {
    const companies = await API.get("/companies");
    if (companyFilter && companies) {
      companyFilter.innerHTML = `<option value="">All Companies</option>` + 
        companies.map(c => `<option value="${c.id}">${c.name}</option>`).join("");
    }
  } catch (e) {}

  const handleFilterChange = () => {
    const search = searchInput ? searchInput.value.trim() : "";
    const status = statusFilter ? statusFilter.value : "";
    const company_id = companyFilter ? companyFilter.value : "";
    const has_followup = followupFilter ? followupFilter.value : "";

    loadContacts({ search, status, company_id, has_followup });
  };

  if (searchInput) {
    let timeout = null;
    searchInput.oninput = () => {
      clearTimeout(timeout);
      timeout = setTimeout(handleFilterChange, 300);
    };
  }
  if (statusFilter) statusFilter.onchange = handleFilterChange;
  if (companyFilter) companyFilter.onchange = handleFilterChange;
  if (followupFilter) followupFilter.onchange = handleFilterChange;

  if (clearFiltersBtn) {
    clearFiltersBtn.onclick = () => {
      if (searchInput) searchInput.value = "";
      if (statusFilter) statusFilter.value = "";
      if (companyFilter) companyFilter.value = "";
      if (followupFilter) followupFilter.value = "";
      loadContacts();
    };
  }

  loadContacts();
}

async function loadContacts(filters = {}) {
  try {
    let url = "/contacts?";
    if (filters.search) url += `search=${encodeURIComponent(filters.search)}&`;
    if (filters.status) url += `status=${encodeURIComponent(filters.status)}&`;
    if (filters.company_id) url += `company_id=${encodeURIComponent(filters.company_id)}&`;
    if (filters.has_followup) url += `has_followup=${encodeURIComponent(filters.has_followup)}&`;

    const contacts = await API.get(url);
    const container = document.getElementById("contacts-table-container");

    if (!contacts || contacts.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <span class="empty-state-icon">👤</span>
          <div class="empty-state-title">No HR contacts found</div>
          <div class="empty-state-description">Add your HR contacts to log calls, schedule Next Move follow-ups, and track job opportunities.</div>
          <button id="empty-add-contact-btn" class="btn btn-primary">+ Add HR Contact</button>
        </div>
      `;
      const emptyBtn = document.getElementById("empty-add-contact-btn");
      if (emptyBtn) emptyBtn.onclick = () => openAddEditContactModal();
      return;
    }

    container.innerHTML = `
      <div class="table-responsive">
        <table>
          <thead>
            <tr>
              <th>HR IDENTITY</th>
              <th>COMPANY</th>
              <th>CONTACT INFO</th>
              <th>STATUS</th>
              <th>LAST INTERACTION</th>
              <th>NEXT MOVE</th>
              <th>OPPORTUNITY</th>
              <th style="text-align: right;">ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            ${contacts.map(c => {
              const initials = c.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
              return `
                <tr class="contact-row" data-id="${c.id}" style="cursor: pointer;">
                  <td>
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                      <div class="contact-avatar">${initials}</div>
                      <div>
                        <div style="font-weight: 600; color: var(--text-primary);">${c.name}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">${c.designation || 'HR Representative'}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <div style="font-weight: 500; color: var(--text-secondary);">${c.company ? c.company.name : '—'}</div>
                  </td>
                  <td>
                    <div>
                      ${c.phone ? `<a href="tel:${c.phone}" class="tel-link" onclick="event.stopPropagation();" style="color: var(--primary-color); text-decoration: none; font-weight: 500;">📞 ${c.phone}</a>` : '<span style="color: var(--text-muted);">—</span>'}
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">
                      ${c.email ? `<a href="mailto:${c.email}" onclick="event.stopPropagation();" style="color: var(--text-muted); text-decoration: none;">✉ ${c.email}</a>` : ''}
                    </div>
                  </td>
                  <td>${formatBadge(c.status)}</td>
                  <td>
                    ${c.last_call_at ? `
                      <div style="font-size: 0.825rem; font-weight: 500;">${formatRelativeTime(c.last_call_at)}</div>
                      <div style="font-size: 0.725rem; color: var(--text-muted);">${c.last_call_outcome ? c.last_call_outcome.replace(/_/g, ' ') : ''}</div>
                    ` : '<span style="color: var(--text-muted); font-size: 0.8rem;">No calls yet</span>'}
                  </td>
                  <td>
                    ${c.next_followup_date ? `
                      <div style="font-size: 0.825rem; font-weight: 600; color: var(--warning-color);">
                        ⚡ ${new Date(c.next_followup_date).toLocaleDateString()}
                      </div>
                      <div style="font-size: 0.725rem; color: var(--text-muted); text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 140px;" title="${c.next_followup_title || ''}">
                        ${c.next_followup_title || ''}
                      </div>
                    ` : '<span style="color: var(--text-muted); font-size: 0.8rem;">No follow-up set</span>'}
                  </td>
                  <td>
                    ${c.active_opportunities_count > 0 ? `
                      <span class="badge-status badge-success" style="font-size: 0.75rem;">💼 ${c.active_opportunities_count} Active</span>
                    ` : '<span style="color: var(--text-muted); font-size: 0.8rem;">—</span>'}
                  </td>
                  <td style="text-align: right;" onclick="event.stopPropagation();">
                    <div style="display: flex; gap: 0.35rem; justify-content: flex-end;">
                      <button class="btn btn-primary log-call-btn" data-id="${c.id}" data-name="${c.name}" title="Log Call" style="font-size: 0.75rem; padding: 0.3rem 0.55rem;">📞 Call</button>
                      <button class="btn btn-outline view-detail-btn" data-id="${c.id}" title="View 360 Detail" style="font-size: 0.75rem; padding: 0.3rem 0.55rem;">👁 View</button>
                      <button class="btn btn-outline edit-contact-btn" data-id="${c.id}" title="Edit Contact" style="font-size: 0.75rem; padding: 0.3rem 0.55rem;">✏️</button>
                    </div>
                  </td>
                </tr>
              `;
            }).join("")}
          </tbody>
        </table>
      </div>
    `;

    // Row click -> 360 Detail Drawer
    container.querySelectorAll(".contact-row").forEach(row => {
      row.onclick = () => {
        const id = row.getAttribute("data-id");
        openContactDetailDrawer(id);
      };
    });

    container.querySelectorAll(".log-call-btn").forEach(btn => {
      btn.onclick = (e) => {
        e.stopPropagation();
        const id = btn.getAttribute("data-id");
        const name = btn.getAttribute("data-name");
        openLogCallModal(id, name);
      };
    });

    container.querySelectorAll(".view-detail-btn").forEach(btn => {
      btn.onclick = (e) => {
        e.stopPropagation();
        const id = btn.getAttribute("data-id");
        openContactDetailDrawer(id);
      };
    });

    container.querySelectorAll(".edit-contact-btn").forEach(btn => {
      btn.onclick = async (e) => {
        e.stopPropagation();
        const id = btn.getAttribute("data-id");
        openAddEditContactModal(id);
      };
    });

  } catch (err) {
    showToast(err.message, "danger");
  }
}

export async function openContactDetailDrawer(contactId) {
  try {
    const data = await API.get(`/contacts/${contactId}/timeline`);
    const c = data.contact;
    const initials = c.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();

    const drawerContent = `
      <!-- PROFILE HEADER CARD -->
      <div style="background-color: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-lg); padding: 1.25rem; margin-bottom: 1.5rem;">
        <div style="display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem;">
          <div class="contact-avatar" style="width: 54px; height: 54px; font-size: 1.35rem;">${initials}</div>
          <div>
            <h2 style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary); margin: 0;">${c.name}</h2>
            <div style="font-size: 0.875rem; color: var(--text-secondary);">${c.designation || 'HR Representative'} • <strong>${c.company ? c.company.name : 'No Company'}</strong></div>
            <div style="margin-top: 0.35rem;">${formatBadge(c.status)}</div>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; font-size: 0.85rem; border-top: 1px solid var(--border-color); padding-top: 0.875rem; margin-top: 0.875rem;">
          <div>
            <span style="color: var(--text-muted);">Phone:</span>
            ${c.phone ? `<a href="tel:${c.phone}" style="display: block; font-weight: 600; color: var(--primary-color); text-decoration: none;">📞 ${c.phone}</a>` : '—'}
          </div>
          <div>
            <span style="color: var(--text-muted);">Email:</span>
            ${c.email ? `<a href="mailto:${c.email}" style="display: block; font-weight: 500; color: var(--text-primary); text-decoration: none;">✉ ${c.email}</a>` : '—'}
          </div>
          <div>
            <span style="color: var(--text-muted);">Location:</span>
            <div style="font-weight: 500; color: var(--text-primary);">${c.location || '—'}</div>
          </div>
          <div>
            <span style="color: var(--text-muted);">LinkedIn:</span>
            ${c.linkedin_url ? `<a href="${c.linkedin_url}" target="_blank" style="display: block; color: var(--primary-color); text-decoration: underline;">LinkedIn Profile 🔗</a>` : '—'}
          </div>
        </div>
      </div>

      <!-- RELATIONSHIP SUMMARY KPIS -->
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; margin-bottom: 1.5rem;">
        <div style="background-color: var(--bg-card); border: 1px solid var(--border-color); padding: 0.75rem; border-radius: var(--radius-md); text-align: center;">
          <div style="font-size: 0.75rem; color: var(--text-muted);">TOTAL CALLS</div>
          <div style="font-size: 1.25rem; font-weight: 700; color: var(--primary-color); margin-top: 0.25rem;">${c.total_calls_count}</div>
        </div>
        <div style="background-color: var(--bg-card); border: 1px solid var(--border-color); padding: 0.75rem; border-radius: var(--radius-md); text-align: center;">
          <div style="font-size: 0.75rem; color: var(--text-muted);">LAST CALL</div>
          <div style="font-size: 0.85rem; font-weight: 600; color: var(--text-primary); margin-top: 0.35rem;">${formatRelativeTime(c.last_call_at)}</div>
        </div>
        <div style="background-color: var(--bg-card); border: 1px solid var(--border-color); padding: 0.75rem; border-radius: var(--radius-md); text-align: center;">
          <div style="font-size: 0.75rem; color: var(--text-muted);">ACTIVE OPPS</div>
          <div style="font-size: 1.25rem; font-weight: 700; color: var(--accent-color); margin-top: 0.25rem;">${c.active_opportunities_count}</div>
        </div>
      </div>

      <!-- ACTION BUTTONS TOOLBAR -->
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1.5rem;">
        <button id="drawer-call-btn" class="btn btn-primary" style="flex: 1; min-width: 120px;">📞 Call HR</button>
        <button id="drawer-nextmove-btn" class="btn btn-outline" style="flex: 1; min-width: 120px;">⚡ Next Move</button>
        <button id="drawer-opp-btn" class="btn btn-outline" style="flex: 1; min-width: 120px;">💼 + Opportunity</button>
      </div>

      <!-- CHRONOLOGICAL ACTIVITY TIMELINE -->
      <div style="margin-top: 1.5rem;">
        <h3 style="font-size: 1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.75rem; display: flex; align-items: center; justify-content: space-between;">
          <span>Activity Timeline (${data.timeline.length})</span>
        </h3>

        ${data.timeline.length === 0 ? `
          <div style="text-align: center; padding: 2rem 1rem; color: var(--text-muted); background: var(--bg-secondary); border-radius: var(--radius-md);">
            No logged activity yet for ${c.name}. Click "📞 Call HR" to log your first call!
          </div>
        ` : `
          <div class="timeline-container">
            ${data.timeline.map(item => `
              <div class="timeline-item">
                <div class="timeline-dot ${item.type}"></div>
                <div class="timeline-content">
                  <div class="timeline-header">
                    <span class="timeline-title">${item.title}</span>
                    <span class="timeline-time">${new Date(item.timestamp).toLocaleString([], {month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'})}</span>
                  </div>
                  ${item.outcome ? `<div style="margin-bottom: 0.35rem;">${formatBadge(item.outcome)}</div>` : ''}
                  ${item.notes ? `<p style="font-size: 0.85rem; color: var(--text-secondary); margin: 0.25rem 0;">"${item.notes}"</p>` : ''}
                  ${item.description ? `<p style="font-size: 0.85rem; color: var(--text-secondary); margin: 0.25rem 0;">${item.description}</p>` : ''}
                  ${item.priority ? `<span class="badge-status badge-muted" style="font-size: 0.65rem;">Priority: ${item.priority}</span>` : ''}
                </div>
              </div>
            `).join("")}
          </div>
        `}
      </div>
    `;

    const { closeDrawer } = openDrawer(`${c.name} — 360° Profile`, drawerContent);

    // Bind drawer buttons
    const callBtn = document.getElementById("drawer-call-btn");
    const nextMoveBtn = document.getElementById("drawer-nextmove-btn");
    const oppBtn = document.getElementById("drawer-opp-btn");

    if (callBtn) {
      callBtn.onclick = () => {
        closeDrawer();
        openLogCallModal(c.id, c.name);
      };
    }

    if (nextMoveBtn) {
      nextMoveBtn.onclick = () => {
        closeDrawer();
        openLogCallModal(c.id, c.name);
      };
    }

    if (oppBtn) {
      oppBtn.onclick = () => {
        closeDrawer();
        openAddOpportunityModalForContact(c);
      };
    }

  } catch (err) {
    showToast(err.message, "danger");
  }
}

export function openLogCallModal(contactId, contactName) {
  const content = `
    <form id="log-call-form">
      <p style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 1.25rem;">
        Logging interaction for <strong>${contactName}</strong>
      </p>

      <!-- CALL TYPE & DURATION -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.25rem;">
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Call Type</label>
          <select id="modal-call-type" class="form-input">
            <option value="OUTBOUND">Outbound Call</option>
            <option value="INBOUND">Inbound Call</option>
            <option value="DISCOVERY">Discovery Call</option>
            <option value="FOLLOWUP">Follow-up Call</option>
          </select>
        </div>
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Duration (Mins)</label>
          <input type="number" id="modal-call-duration" placeholder="e.g. 5" class="form-input" min="1">
        </div>
      </div>

      <!-- CALL OUTCOME SELECTION CHIPS -->
      <div style="margin-bottom: 1.25rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Select Call Outcome *</label>
        <input type="hidden" id="modal-call-outcome-val" value="CONNECTED">
        
        <div class="outcome-chip-grid">
          <div class="outcome-chip" data-val="OPPORTUNITY_AVAILABLE">💼 Opportunity Open</div>
          <div class="outcome-chip" data-val="RESUME_REQUESTED">📄 Resume Requested</div>
          <div class="outcome-chip selected" data-val="CONNECTED">📞 Connected</div>
          <div class="outcome-chip" data-val="CALL_BACK">🟡 Ask to Call Back</div>
          <div class="outcome-chip" data-val="NO_ANSWER">🚫 No Answer / Busy</div>
          <div class="outcome-chip" data-val="NOT_HIRING">🔴 Not Hiring</div>
          <div class="outcome-chip" data-val="NOT_RELEVANT">❌ Not Relevant</div>
        </div>
      </div>

      <!-- PROMINENT CALL NOTES / REASON -->
      <div style="margin-bottom: 1.25rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">What happened during this call? *</label>
        <textarea id="modal-call-notes" rows="3" required placeholder="HR asked to share updated resume, discussed Automation opening..." class="form-input" style="width: 100%;"></textarea>
      </div>

      <!-- NEXT MOVE FOLLOW-UP CREATION ENGINE -->
      <div style="background-color: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 1rem; margin-top: 1rem;">
        <label style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; font-weight: 700; cursor: pointer; color: var(--text-primary);">
          <input type="checkbox" id="modal-call-create-followup" checked>
          ⚡ Schedule a Next Move Follow-up
        </label>

        <div id="followup-fields" style="margin-top: 0.875rem;">
          <div style="margin-bottom: 0.75rem;">
            <label style="display: block; font-size: 0.8rem; font-weight: 500; margin-bottom: 0.25rem;">Next Action Title</label>
            <input type="text" id="modal-followup-title" value="Follow up call with ${contactName}" class="form-input" style="width: 100%;">
          </div>

          <!-- PRESET DATE SHORTCUTS -->
          <div style="margin-bottom: 0.75rem;">
            <label style="display: block; font-size: 0.8rem; font-weight: 500; margin-bottom: 0.25rem;">Due Date Shortcuts</label>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
              <button type="button" class="btn btn-outline date-preset-btn" data-days="1" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">Tomorrow</button>
              <button type="button" class="btn btn-outline date-preset-btn" data-days="3" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">In 3 Days</button>
              <button type="button" class="btn btn-outline date-preset-btn" data-days="7" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;">Next Week</button>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
            <div>
              <label style="display: block; font-size: 0.8rem; font-weight: 500; margin-bottom: 0.25rem;">Due Date *</label>
              <input type="date" id="modal-followup-date" class="form-input" style="width: 100%;">
            </div>
            <div>
              <label style="display: block; font-size: 0.8rem; font-weight: 500; margin-bottom: 0.25rem;">Priority</label>
              <select id="modal-followup-priority" class="form-input" style="width: 100%;">
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High Priority</option>
                <option value="LOW">Low Priority</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </form>
  `;

  openModal("Log HR Call & Next Move", content, async (close) => {
    const call_type = document.getElementById("modal-call-type").value;
    const duration_val = document.getElementById("modal-call-duration").value;
    const duration_minutes = duration_val ? parseInt(duration_val, 10) : null;
    const outcome = document.getElementById("modal-call-outcome-val").value;
    const notes = document.getElementById("modal-call-notes").value.trim();

    if (!notes) {
      showToast("Call notes are required.", "danger");
      return;
    }

    const create_followup = document.getElementById("modal-call-create-followup").checked;
    const followup_title = document.getElementById("modal-followup-title").value.trim();
    const followup_date_val = document.getElementById("modal-followup-date").value;
    const followup_priority = document.getElementById("modal-followup-priority").value;

    let followup_due_date = null;
    if (create_followup && followup_date_val) {
      followup_due_date = new Date(followup_date_val).toISOString();
    }

    try {
      await API.post("/activity/calls", {
        contact_id: parseInt(contactId, 10),
        call_type,
        outcome,
        duration_minutes,
        notes,
        create_followup,
        followup_title,
        followup_due_date,
        followup_priority
      });

      showToast("Call logged & Next Move recorded!");
      close();
      loadContacts();

      // If Opportunity Available, suggest creating job requirement!
      if (outcome === "OPPORTUNITY_AVAILABLE") {
        setTimeout(async () => {
          try {
            const contact = await API.get(`/contacts/${contactId}`);
            openAddOpportunityModalForContact(contact);
          } catch (e) {}
        }, 300);
      }

    } catch (err) {
      showToast(err.message, "danger");
    }
  });

  // Outcome Chip Selection Logic
  const outcomeValInput = document.getElementById("modal-call-outcome-val");
  const followupTitleInput = document.getElementById("modal-followup-title");
  const chips = document.querySelectorAll(".outcome-chip");

  chips.forEach(chip => {
    chip.onclick = () => {
      chips.forEach(c => c.classList.remove("selected"));
      chip.classList.add("selected");
      const val = chip.getAttribute("data-val");
      outcomeValInput.value = val;

      // Smart title pre-filling
      if (val === "RESUME_REQUESTED") {
        followupTitleInput.value = `Send updated resume to ${contactName}`;
      } else if (val === "OPPORTUNITY_AVAILABLE") {
        followupTitleInput.value = `Follow up on open role with ${contactName}`;
      } else if (val === "CALL_BACK") {
        followupTitleInput.value = `Call back ${contactName}`;
      } else {
        followupTitleInput.value = `Follow up call with ${contactName}`;
      }
    };
  });

  // Set default due date to tomorrow
  const dateInput = document.getElementById("modal-followup-date");
  if (dateInput) {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    dateInput.value = tomorrow.toISOString().split("T")[0];
  }

  // Date preset buttons
  document.querySelectorAll(".date-preset-btn").forEach(btn => {
    btn.onclick = () => {
      const days = parseInt(btn.getAttribute("data-days"), 10);
      const d = new Date();
      d.setDate(d.getDate() + days);
      if (dateInput) dateInput.value = d.toISOString().split("T")[0];
    };
  });
}

function openAddEditContactModal(contactId = null) {
  let isEdit = !!contactId;
  
  const content = `
    <form id="contact-modal-form">
      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Contact Name *</label>
        <input type="text" id="modal-contact-name" required placeholder="e.g. Priya Sharma" class="form-input" style="width: 100%;">
      </div>
      
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Company Name</label>
          <input type="text" id="modal-contact-company" placeholder="e.g. Infosys" class="form-input" style="width: 100%;">
        </div>
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Designation</label>
          <input type="text" id="modal-contact-designation" placeholder="Senior Recruiter" class="form-input" style="width: 100%;">
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Phone Number</label>
          <input type="text" id="modal-contact-phone" placeholder="+91 98765 43210" class="form-input" style="width: 100%;">
        </div>
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Email Address</label>
          <input type="email" id="modal-contact-email" placeholder="priya@company.com" class="form-input" style="width: 100%;">
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">LinkedIn Profile URL</label>
          <input type="text" id="modal-contact-linkedin" placeholder="https://linkedin.com/in/..." class="form-input" style="width: 100%;">
        </div>
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Location</label>
          <input type="text" id="modal-contact-location" placeholder="Bengaluru / Remote" class="form-input" style="width: 100%;">
        </div>
      </div>

      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Relationship Notes</label>
        <textarea id="modal-contact-notes" rows="2" placeholder="Initial context or notes..." class="form-input" style="width: 100%;"></textarea>
      </div>
    </form>
  `;

  openModal(isEdit ? "Edit HR Contact" : "Add HR Contact", content, async (close) => {
    const name = document.getElementById("modal-contact-name").value.trim();
    if (!name) {
      showToast("Contact name is required.", "danger");
      return;
    }
    const company_name = document.getElementById("modal-contact-company").value.trim();
    const designation = document.getElementById("modal-contact-designation").value.trim();
    const phone = document.getElementById("modal-contact-phone").value.trim();
    const email = document.getElementById("modal-contact-email").value.trim();
    const linkedin_url = document.getElementById("modal-contact-linkedin").value.trim();
    const location = document.getElementById("modal-contact-location").value.trim();
    const notes = document.getElementById("modal-contact-notes").value.trim();

    try {
      if (isEdit) {
        await API.put(`/contacts/${contactId}`, { name, designation, phone, email, linkedin_url, location, notes });
        showToast("HR Contact updated!");
      } else {
        await API.post("/contacts", { name, company_name, designation, phone, email, linkedin_url, location, notes });
        showToast("HR Contact created!");
      }
      close();
      loadContacts();
    } catch (err) {
      showToast(err.message, "danger");
    }
  });

  if (isEdit) {
    API.get(`/contacts/${contactId}`).then(c => {
      document.getElementById("modal-contact-name").value = c.name || "";
      document.getElementById("modal-contact-company").value = c.company ? c.company.name : "";
      document.getElementById("modal-contact-designation").value = c.designation || "";
      document.getElementById("modal-contact-phone").value = c.phone || "";
      document.getElementById("modal-contact-email").value = c.email || "";
      document.getElementById("modal-contact-linkedin").value = c.linkedin_url || "";
      document.getElementById("modal-contact-location").value = c.location || "";
      document.getElementById("modal-contact-notes").value = c.notes || "";
    }).catch(err => showToast("Failed to load contact data.", "danger"));
  }
}

function openAddOpportunityModalForContact(contact) {
  const content = `
    <form id="opportunity-modal-form">
      <p style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 1rem;">
        Creating Opportunity for HR <strong>${contact.name}</strong> (${contact.company ? contact.company.name : 'Company'})
      </p>

      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Job Role Title *</label>
        <input type="text" id="modal-opp-title" required placeholder="e.g. Senior QA Automation Engineer" class="form-input" style="width: 100%;">
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Location</label>
          <input type="text" id="modal-opp-location" value="${contact.location || ''}" placeholder="Bengaluru / Remote" class="form-input" style="width: 100%;">
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
        <input type="text" id="modal-opp-skills" placeholder="Python, Selenium, Pytest, REST APIs" class="form-input" style="width: 100%;">
      </div>

      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Description / Requirement Notes</label>
        <textarea id="modal-opp-desc" rows="3" placeholder="Details discussed with HR..." class="form-input" style="width: 100%;"></textarea>
      </div>
    </form>
  `;

  openModal("Create Job Opportunity", content, async (close) => {
    const title = document.getElementById("modal-opp-title").value.trim();
    if (!title) {
      showToast("Job title is required.", "danger");
      return;
    }
    if (!contact.company_id) {
      showToast("Contact must be linked to a company to attach opportunity.", "danger");
      return;
    }

    const location = document.getElementById("modal-opp-location").value.trim();
    const employment_type = document.getElementById("modal-opp-type").value;
    const skills_req = document.getElementById("modal-opp-skills").value.trim();
    const description = document.getElementById("modal-opp-desc").value.trim();

    try {
      await API.post("/requirements", {
        company_id: contact.company_id,
        contact_id: contact.id,
        title,
        location,
        employment_type,
        skills_req,
        description
      });

      showToast("Opportunity created!");
      close();
      loadContacts();
    } catch (err) {
      showToast(err.message, "danger");
    }
  });
}
