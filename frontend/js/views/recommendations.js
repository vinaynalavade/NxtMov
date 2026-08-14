import { api } from "../api.js";
import { showToast } from "../components.js";

export function renderRecommendations() {
  return `
    <div class="view-header">
      <div>
        <h1 class="view-title">🎯 Intelligent Role Matching & Recommendations</h1>
        <p class="view-subtitle">Weighted AI matching algorithm connects your candidate profile with live job requirements. Sort by match score and apply with 1 click.</p>
      </div>
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
        <button class="btn btn-outline rec-filter-btn active" data-filter="ALL">All Open Roles</button>
        <button class="btn btn-outline rec-filter-btn" data-filter="BEST_MATCHES">⭐ Best Matches (75%+)</button>
        <button class="btn btn-outline rec-filter-btn" data-filter="SAVED">🔖 Saved Roles</button>
        <button class="btn btn-outline rec-filter-btn" data-filter="APPLIED">✅ Applied Roles</button>
      </div>
    </div>

    <!-- Recommendations Grid Container -->
    <div id="recommendations-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 1.5rem;">
      <div style="text-align: center; grid-column: 1 / -1; padding: 3rem; color: var(--text-muted);">
        ⏳ Calculating role matches and weighted scoring...
      </div>
    </div>
  `;
}

export function initRecommendationsListeners() {
  let currentFilter = "ALL";

  const filterBtns = document.querySelectorAll(".rec-filter-btn");
  filterBtns.forEach(btn => {
    btn.onclick = () => {
      filterBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentFilter = btn.getAttribute("data-filter");
      loadRecommendations(currentFilter);
    };
  });

  loadRecommendations(currentFilter);
}

async function loadRecommendations(filterType = "ALL") {
  const container = document.getElementById("recommendations-grid");
  if (!container) return;

  try {
    const recs = await api.get(`/recommendations?filter_type=${filterType}`);
    if (!recs || recs.length === 0) {
      container.innerHTML = `
        <div class="card" style="text-align: center; grid-column: 1 / -1; padding: 3rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔍</div>
          <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary);">No matching roles found</h3>
          <p style="font-size: 0.85rem; color: var(--text-muted); max-width: 400px; margin: 0 auto;">
            Try updating your preferred roles, skills, or location in your Student Profile to discover more recommendations.
          </p>
        </div>
      `;
      return;
    }

    container.innerHTML = recs.map(r => {
      const matchPct = Math.round(r.match_score);
      let matchColor = "var(--primary-color)";
      if (matchPct >= 80) matchColor = "var(--accent-color)";
      else if (matchPct < 65) matchColor = "var(--warning-color)";

      return `
        <div class="card" style="display: flex; flex-direction: column; justify-content: space-between; border-top: 4px solid ${matchColor};">
          <div>
            <!-- Header Row -->
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
              <div>
                <span class="badge-status badge-info" style="font-size: 0.7rem; margin-bottom: 0.25rem; display: inline-block;">${r.company_name}</span>
                <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin: 0;">${r.title}</h3>
                <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.15rem;">
                  📍 ${r.location || 'Location flexible'} • ${r.work_mode} • ${r.employment_type}
                </div>
              </div>

              <!-- Match Badge -->
              <div style="text-align: center; background-color: rgba(16, 185, 129, 0.1); border: 1px solid ${matchColor}; padding: 0.35rem 0.65rem; border-radius: var(--radius-md);">
                <div style="font-size: 1.15rem; font-weight: 800; color: ${matchColor};">${matchPct}%</div>
                <div style="font-size: 0.65rem; font-weight: 700; color: var(--text-secondary); text-transform: uppercase;">Match</div>
              </div>
            </div>

            <!-- Skills Badges -->
            <div style="margin-bottom: 1rem;">
              <div style="font-size: 0.75rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 0.35rem;">Matched Skills:</div>
              <div style="display: flex; gap: 0.35rem; flex-wrap: wrap;">
                ${r.matched_skills.map(s => `<span class="badge-status badge-success" style="font-size: 0.68rem;">✓ ${s}</span>`).join("")}
                ${r.missing_skills.map(s => `<span class="badge-status badge-muted" style="font-size: 0.68rem;">⚠ ${s}</span>`).join("")}
              </div>
            </div>

            <!-- Why This Role Matches Accordion -->
            <div style="background-color: var(--bg-secondary); border-radius: var(--radius-md); padding: 0.75rem; margin-bottom: 1rem; font-size: 0.775rem;">
              <div style="font-weight: 700; color: var(--accent-color); margin-bottom: 0.25rem;">Why this role matches:</div>
              <ul style="padding-left: 1rem; margin: 0 0 0.5rem 0; color: var(--text-secondary);">
                ${r.why_matches.map(w => `<li>${w}</li>`).join("")}
              </ul>
              ${r.what_is_missing && r.what_is_missing.length > 0 ? `
                <div style="font-weight: 700; color: var(--warning-color); margin-bottom: 0.25rem;">What is missing:</div>
                <ul style="padding-left: 1rem; margin: 0; color: var(--text-muted);">
                  ${r.what_is_missing.map(m => `<li>${m}</li>`).join("")}
                </ul>
              ` : ''}
            </div>
          </div>

          <!-- Card Actions -->
          <div style="display: flex; gap: 0.5rem; justify-content: space-between; border-top: 1px solid var(--border-color); padding-top: 0.75rem;">
            <button class="btn btn-outline save-rec-btn" data-id="${r.id}" style="font-size: 0.8rem; padding: 0.35rem 0.65rem;">
              ${r.is_saved ? '🔖 Saved' : '🤍 Save'}
            </button>
            <div style="display: flex; gap: 0.5rem;">
              <button class="btn btn-outline dismiss-rec-btn" data-id="${r.id}" style="font-size: 0.8rem; padding: 0.35rem 0.65rem;">Dismiss</button>
              ${r.is_applied ? `
                <button class="btn btn-outline" disabled style="font-size: 0.8rem; padding: 0.35rem 0.75rem;">✅ Applied</button>
              ` : `
                <button class="btn btn-primary apply-rec-btn" data-req-id="${r.job_requirement_id}" style="font-size: 0.8rem; padding: 0.35rem 0.75rem;">⚡ 1-Click Apply</button>
              `}
            </div>
          </div>
        </div>
      `;
    }).join("");

    // Attach Action Listeners
    container.querySelectorAll(".save-rec-btn").forEach(btn => {
      btn.onclick = async () => {
        const id = btn.getAttribute("data-id");
        try {
          const res = await api.post(`/recommendations/${id}/save`);
          showToast(res.is_saved ? "Role saved to your shortlist!" : "Role unsaved.");
          loadRecommendations(filterType);
        } catch (err) {
          showToast("Failed to save role.", "danger");
        }
      };
    });

    container.querySelectorAll(".dismiss-rec-btn").forEach(btn => {
      btn.onclick = async () => {
        const id = btn.getAttribute("data-id");
        try {
          await api.post(`/recommendations/${id}/dismiss`);
          showToast("Recommendation dismissed.");
          loadRecommendations(filterType);
        } catch (err) {
          showToast("Failed to dismiss role.", "danger");
        }
      };
    });

    container.querySelectorAll(".apply-rec-btn").forEach(btn => {
      btn.onclick = async () => {
        const reqId = parseInt(btn.getAttribute("data-req-id"));
        try {
          btn.disabled = true;
          btn.textContent = "⏳ Applying...";
          await api.post("/applications", { job_requirement_id: reqId });
          showToast("Application submitted successfully!");
          loadRecommendations(filterType);
        } catch (err) {
          btn.disabled = false;
          btn.textContent = "⚡ 1-Click Apply";
          showToast(err.message || "Failed to submit application.", "danger");
        }
      };
    });

  } catch (err) {
    showToast(err.message || "Failed to load role recommendations.", "danger");
  }
}
