import { api } from "../api.js";
import { showToast, createModal } from "../components.js";

export function renderTeamView(container) {
  container.innerHTML = `
    <div style="max-width: 1200px; margin: 0 auto;">
      <div class="view-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
          <h2 style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.25rem;">Team Management</h2>
          <p style="color: var(--text-secondary); font-size: 0.875rem;">Manage consultancy recruiters, counselors, and organization members.</p>
        </div>
        <button id="invite-member-btn" class="btn btn-primary">+ Invite Team Member</button>
      </div>

      <div class="card" style="margin-bottom: 1.5rem;">
        <h3 style="font-size: 1.1rem; margin-bottom: 1rem;">Active Team Members</h3>
        <div id="team-members-list" class="table-responsive">
          <p style="color: var(--text-muted);">Loading team members...</p>
        </div>
      </div>

      <div class="card">
        <h3 style="font-size: 1.1rem; margin-bottom: 1rem;">Pending Invitations</h3>
        <div id="pending-invitations-list" class="table-responsive">
          <p style="color: var(--text-muted);">Loading invitations...</p>
        </div>
      </div>
    </div>
  `;

  loadTeamData();

  document.getElementById("invite-member-btn")?.addEventListener("click", openInviteModal);
}

async function loadTeamData() {
  const listContainer = document.getElementById("team-members-list");
  const invContainer = document.getElementById("pending-invitations-list");

  try {
    const [team, invitations] = await Promise.all([
      api.get("/organizations/team"),
      api.get("/organizations/invitations")
    ]);

    // Render Team Members
    if (team.length === 0) {
      listContainer.innerHTML = `<p style="color: var(--text-muted);">No team members found.</p>`;
    } else {
      listContainer.innerHTML = `
        <table style="width: 100%; border-collapse: collapse; text-align: left;">
          <thead>
            <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-secondary); font-size: 0.85rem;">
              <th style="padding: 0.75rem;">MEMBER NAME</th>
              <th style="padding: 0.75rem;">EMAIL</th>
              <th style="padding: 0.75rem;">ROLE</th>
              <th style="padding: 0.75rem;">JOINED DATE</th>
            </tr>
          </thead>
          <tbody>
            ${team.map(m => `
              <tr style="border-bottom: 1px solid var(--border-color); font-size: 0.9rem;">
                <td style="padding: 0.875rem; font-weight: 600;">${m.full_name}</td>
                <td style="padding: 0.875rem; color: var(--text-secondary);">${m.email}</td>
                <td style="padding: 0.875rem;"><span class="badge badge-info">${m.role}</span></td>
                <td style="padding: 0.875rem; color: var(--text-muted);">${new Date(m.joined_at).toLocaleDateString()}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    }

    // Render Invitations
    if (invitations.length === 0) {
      invContainer.innerHTML = `<p style="color: var(--text-muted);">No pending invitations.</p>`;
    } else {
      invContainer.innerHTML = `
        <table style="width: 100%; border-collapse: collapse; text-align: left;">
          <thead>
            <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-secondary); font-size: 0.85rem;">
              <th style="padding: 0.75rem;">INVITED EMAIL</th>
              <th style="padding: 0.75rem;">ROLE</th>
              <th style="padding: 0.75rem;">STATUS</th>
              <th style="padding: 0.75rem;">INVITATION TOKEN</th>
              <th style="padding: 0.75rem; text-align: right;">ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            ${invitations.map(i => `
              <tr style="border-bottom: 1px solid var(--border-color); font-size: 0.9rem;">
                <td style="padding: 0.875rem; font-weight: 600;">${i.email}</td>
                <td style="padding: 0.875rem;"><span class="badge badge-warning">${i.role}</span></td>
                <td style="padding: 0.875rem; color: var(--text-secondary);">${i.status}</td>
                <td style="padding: 0.875rem; font-family: monospace; font-size: 0.75rem; color: var(--primary-color);">${i.token.substring(0, 16)}...</td>
                <td style="padding: 0.875rem; text-align: right;">
                  <button class="btn btn-outline revoke-inv-btn" data-id="${i.id}" style="font-size: 0.75rem; padding: 0.25rem 0.5rem; color: var(--error-color);">Revoke</button>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;

      invContainer.querySelectorAll(".revoke-inv-btn").forEach(btn => {
        btn.addEventListener("click", async (e) => {
          const invId = e.target.dataset.id;
          try {
            await api.delete(`/organizations/invitations/${invId}`);
            showToast("Invitation revoked.");
            loadTeamData();
          } catch (err) {
            showToast(err.message || "Failed to revoke invitation.", "error");
          }
        });
      });
    }

  } catch (err) {
    showToast("Failed to load team data.", "error");
  }
}

function openInviteModal() {
  const content = `
    <form id="invite-form" style="display: flex; flex-direction: column; gap: 1rem;">
      <div class="form-group">
        <label>Member Email *</label>
        <input type="email" id="inv-email" required placeholder="colleague@agency.com" class="form-control" />
      </div>
      <div class="form-group">
        <label>Organization Role *</label>
        <select id="inv-role" class="form-control" required>
          <option value="RECRUITER">Recruiter</option>
          <option value="COUNSELOR">Counselor</option>
          <option value="ADMIN">Admin</option>
          <option value="CANDIDATE">Candidate</option>
        </select>
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1rem;">
        <button type="button" class="btn btn-outline close-modal-btn">Cancel</button>
        <button type="submit" class="btn btn-primary">Send Invitation</button>
      </div>
    </form>
  `;

  const { closeModal } = createModal("Invite Team Member", content);

  document.getElementById("invite-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("inv-email").value.trim();
    const role = document.getElementById("inv-role").value;

    try {
      await api.post("/organizations/invitations", { email, role });
      showToast(`Invitation sent to ${email}`);
      closeModal();
      loadTeamData();
    } catch (err) {
      showToast(err.message || "Failed to send invitation.", "error");
    }
  });
}
