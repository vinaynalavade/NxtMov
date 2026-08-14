import { API } from "../api.js";
import { showToast, openModal, formatBadge, formatRelativeTime } from "../components.js";
import { openContactDetailDrawer, openLogCallModal } from "./contacts.js";

export function renderFollowups() {
  return `
    <div class="view-header">
      <div>
        <h1 class="view-title">⚡ Next Move Engine (Follow-ups)</h1>
        <p class="view-subtitle">Action items and scheduled follow-ups with HR contacts and recruiters.</p>
      </div>
      <button id="add-followup-btn" class="btn btn-primary">+ Add Follow-up Task</button>
    </div>

    <!-- Filter Tab Bar -->
    <div class="card" style="margin-bottom: 1.5rem; padding: 0.5rem; display: flex; gap: 0.5rem; overflow-x: auto; background-color: var(--bg-card);">
      <button class="filter-tab btn btn-outline active-tab" data-type="today">Due Today</button>
      <button class="filter-tab btn btn-outline" data-type="overdue">Overdue</button>
      <button class="filter-tab btn btn-outline" data-type="upcoming">Upcoming</button>
      <button class="filter-tab btn btn-outline" data-type="completed">Completed</button>
      <button class="filter-tab btn btn-outline" data-type="all">All Tasks</button>
    </div>

    <div class="card">
      <div id="followups-list-container">
        <p style="color: var(--text-muted); text-align: center; padding: 2rem;">Loading action items...</p>
      </div>
    </div>
  `;
}

export async function initFollowupsListeners() {
  const addBtn = document.getElementById("add-followup-btn");
  if (addBtn) addBtn.onclick = () => openAddFollowupModal();

  const tabs = document.querySelectorAll(".filter-tab");
  tabs.forEach(tab => {
    tab.onclick = () => {
      tabs.forEach(t => t.classList.remove("active-tab"));
      tab.classList.add("active-tab");
      const filterType = tab.getAttribute("data-type");
      loadFollowups(filterType);
    };
  });

  loadFollowups("today");
}

async function loadFollowups(filterType = "today") {
  try {
    const followups = await API.get(`/activity/followups?filter_type=${filterType}`);
    const container = document.getElementById("followups-list-container");

    if (!followups || followups.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <span class="empty-state-icon">🎉</span>
          <div class="empty-state-title">No tasks found for this category</div>
          <div class="empty-state-description">You are all caught up! Log a call or add a contact to schedule your Next Move.</div>
          <button id="empty-fup-btn" class="btn btn-primary">+ Add Follow-up Task</button>
        </div>
      `;
      const emptyBtn = document.getElementById("empty-fup-btn");
      if (emptyBtn) emptyBtn.onclick = () => openAddFollowupModal();
      return;
    }

    const now = new Date();

    container.innerHTML = followups.map(f => {
      const isOverdue = f.status === 'PENDING' && new Date(f.due_date) < now;
      const isCompleted = f.status === 'COMPLETED';

      return `
        <div class="followup-card-item" style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 1rem; padding: 1.25rem; border-bottom: 1px solid var(--border-color); background-color: ${isOverdue ? 'rgba(239, 68, 68, 0.04)' : 'transparent'}; border-left: ${isOverdue ? '4px solid var(--danger-color)' : 'none'};">
          <div style="flex: 1; min-width: 260px;">
            <div style="display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;">
              <span style="font-weight: 700; font-size: 1.05rem; ${isCompleted ? 'text-decoration: line-through; opacity: 0.6;' : ''}">${f.title}</span>
              ${formatBadge(f.status)}
              <span class="badge-status ${f.priority === 'HIGH' ? 'badge-danger' : f.priority === 'LOW' ? 'badge-muted' : 'badge-warning'}" style="font-size: 0.7rem;">${f.priority} PRIORITY</span>
            </div>

            <!-- WHO & WHERE -->
            ${f.contact_name ? `
              <div style="font-size: 0.875rem; font-weight: 600; color: var(--primary-color); margin-top: 0.35rem;">
                👤 ${f.contact_name} ${f.company_name ? `• <span style="color: var(--text-secondary); font-weight: 500;">${f.company_name}</span>` : ''}
              </div>
            ` : ''}

            <!-- WHY (Description / Notes) -->
            ${f.description ? `
              <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.35rem; font-style: italic;">
                "${f.description}"
              </p>
            ` : ''}

            <!-- WHEN -->
            <div style="font-size: 0.775rem; color: ${isOverdue ? 'var(--danger-color)' : 'var(--text-muted)'}; font-weight: ${isOverdue ? '700' : '500'}; margin-top: 0.5rem;">
              📅 Due: <strong>${new Date(f.due_date).toLocaleDateString()} at ${new Date(f.due_date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</strong>
              ${isOverdue ? ' (Overdue!)' : ''}
            </div>
          </div>

          <!-- DIRECT ACTIONS -->
          <div style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;">
            ${f.phone ? `
              <a href="tel:${f.phone}" class="btn btn-outline" style="font-size: 0.75rem; padding: 0.35rem 0.65rem; text-decoration: none; color: var(--primary-color);">📞 Call ${f.phone}</a>
            ` : ''}

            ${f.entity_id && f.entity_type === 'CONTACT' ? `
              <button class="btn btn-outline view-contact-btn" data-contact-id="${f.entity_id}" style="font-size: 0.75rem; padding: 0.35rem 0.65rem;">👁 Contact</button>
              <button class="btn btn-outline log-call-btn" data-contact-id="${f.entity_id}" data-contact-name="${f.contact_name || 'HR'}" style="font-size: 0.75rem; padding: 0.35rem 0.65rem;">📝 Log Call</button>
            ` : ''}

            ${f.status === 'PENDING' ? `
              <button class="btn btn-primary toggle-complete-btn" data-id="${f.id}" style="font-size: 0.75rem; padding: 0.35rem 0.75rem;">✓ Mark Done</button>
            ` : `
              <button class="btn btn-outline toggle-complete-btn" data-id="${f.id}" style="font-size: 0.75rem; padding: 0.35rem 0.75rem;">↩ Undo</button>
            `}
          </div>
        </div>
      `;
    }).join("");

    container.querySelectorAll(".toggle-complete-btn").forEach(btn => {
      btn.onclick = async () => {
        const id = btn.getAttribute("data-id");
        const currentText = btn.textContent.trim();
        const newStatus = currentText.includes("Mark Done") ? "COMPLETED" : "PENDING";
        
        try {
          await API.put(`/activity/followups/${id}`, { status: newStatus });
          showToast(`Task marked as ${newStatus}!`);
          loadFollowups(filterType);
        } catch (err) {
          showToast(err.message, "danger");
        }
      };
    });

    container.querySelectorAll(".view-contact-btn").forEach(btn => {
      btn.onclick = () => {
        const contactId = btn.getAttribute("data-contact-id");
        openContactDetailDrawer(contactId);
      };
    });

    container.querySelectorAll(".log-call-btn").forEach(btn => {
      btn.onclick = () => {
        const contactId = btn.getAttribute("data-contact-id");
        const name = btn.getAttribute("data-contact-name");
        openLogCallModal(contactId, name);
      };
    });

  } catch (err) {
    showToast(err.message, "danger");
  }
}

async function openAddFollowupModal() {
  let contacts = [];
  try {
    contacts = await API.get("/contacts");
  } catch (e) {}

  const content = `
    <form id="followup-modal-form">
      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Link HR Contact (Optional)</label>
        <select id="modal-fup-contact" class="form-input" style="width: 100%;">
          <option value="">-- Select Contact --</option>
          ${contacts.map(c => `<option value="${c.id}">${c.name} (${c.company ? c.company.name : 'Company'})</option>`).join("")}
        </select>
      </div>

      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Action Task Title *</label>
        <input type="text" id="modal-fup-title" required placeholder="e.g. Follow up on resume review with Infosys HR" class="form-input" style="width: 100%;">
      </div>

      <div style="margin-bottom: 1rem;">
        <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Description / Notes</label>
        <textarea id="modal-fup-desc" rows="2" placeholder="Specific questions or next steps..." class="form-input" style="width: 100%;"></textarea>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Due Date *</label>
          <input type="date" id="modal-fup-date" required class="form-input" style="width: 100%;">
        </div>
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">Priority</label>
          <select id="modal-fup-priority" class="form-input" style="width: 100%;">
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High Priority</option>
            <option value="LOW">Low Priority</option>
          </select>
        </div>
      </div>
    </form>
  `;

  openModal("Add Next Move Task", content, async (close) => {
    const title = document.getElementById("modal-fup-title").value.trim();
    const dateVal = document.getElementById("modal-fup-date").value;
    if (!title || !dateVal) {
      showToast("Title and Due Date are required.", "danger");
      return;
    }

    const contactIdVal = document.getElementById("modal-fup-contact").value;
    const description = document.getElementById("modal-fup-desc").value.trim();
    const priority = document.getElementById("modal-fup-priority").value;
    const due_date = new Date(dateVal).toISOString();

    const entity_type = contactIdVal ? "CONTACT" : null;
    const entity_id = contactIdVal ? parseInt(contactIdVal, 10) : null;

    try {
      await API.post("/activity/followups", { title, description, due_date, priority, entity_type, entity_id });
      showToast("Next Move task created!");
      close();
      loadFollowups("today");
    } catch (err) {
      showToast(err.message, "danger");
    }
  });

  const dateInput = document.getElementById("modal-fup-date");
  if (dateInput) {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    dateInput.value = tomorrow.toISOString().split("T")[0];
  }
}
