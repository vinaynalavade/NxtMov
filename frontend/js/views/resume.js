import { api } from "../api.js";
import { showToast } from "../components.js";

export function renderResume() {
  return `
    <div class="view-header">
      <div>
        <h1 class="view-title">📄 Resume Management & AI Quality Intelligence</h1>
        <p class="view-subtitle">Upload your resume, inspect AI-extracted skills/qualification, review your Resume Quality Score, and apply updates to your profile.</p>
      </div>
    </div>

    <!-- Upload Card -->
    <div class="card" style="margin-bottom: 2rem;">
      <div id="resume-drop-zone" style="border: 2px dashed var(--border-hover); border-radius: var(--radius-xl); padding: 2.5rem 1.5rem; text-align: center; background-color: var(--bg-secondary); cursor: pointer;">
        <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📄</div>
        <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.25rem;">Upload or Replace Your Resume</h3>
        <p style="color: var(--text-muted); font-size: 0.825rem; max-width: 460px; margin: 0 auto 1.25rem auto;">
          Supports <strong>.pdf</strong>, <strong>.docx</strong>, and <strong>.txt</strong>. NxtMov automatically extracts skills, education, and experiences.
        </p>
        <input type="file" id="resume-file-input" accept=".pdf,.docx,.txt" style="display: none;" />
        <button id="resume-browse-btn" class="btn btn-primary btn-lg">Browse Resume File</button>
      </div>
    </div>

    <!-- Active Resume Card & Quality Score Container -->
    <div id="active-resume-container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem; margin-bottom: 2rem;">
      <!-- Active Resume Card -->
      <div id="current-resume-card" class="card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
          <div>
            <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary);">Current Active Resume</h3>
            <p id="resume-uploaded-date" style="font-size: 0.775rem; color: var(--text-muted);">No resume uploaded yet</p>
          </div>
          <span id="resume-status-badge" class="badge-status badge-muted">Not Uploaded</span>
        </div>

        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.25rem; background: var(--bg-secondary); padding: 1rem; border-radius: var(--radius-md);">
          <div style="font-size: 2rem;">📑</div>
          <div style="flex: 1; overflow: hidden;">
            <div id="resume-file-name" style="font-weight: 700; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">-</div>
            <div id="resume-file-size" style="font-size: 0.75rem; color: var(--text-muted);">-</div>
          </div>
        </div>

        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
          <a id="resume-view-btn" href="#" target="_blank" class="btn btn-outline" style="font-size: 0.8rem; display: none;">👁️ View File</a>
          <button id="resume-reanalyze-btn" class="btn btn-primary" style="font-size: 0.8rem; display: none;">🔍 Analyze Resume</button>
        </div>
      </div>

      <!-- Resume Quality Score Card -->
      <div id="resume-quality-card" class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary);">Resume Quality Score</h3>
          <div id="quality-score-badge" style="font-size: 1.5rem; font-weight: 800; color: var(--primary-color);">--/100</div>
        </div>

        <div style="margin-bottom: 1rem;">
          <h4 style="font-size: 0.85rem; font-weight: 700; color: var(--accent-color); margin-bottom: 0.35rem;">Strengths</h4>
          <ul id="quality-strengths-list" style="font-size: 0.8rem; color: var(--text-secondary); padding-left: 1.25rem; margin: 0;">
            <li>Upload a resume to calculate quality score</li>
          </ul>
        </div>

        <div>
          <h4 style="font-size: 0.85rem; font-weight: 700; color: var(--warning-color); margin-bottom: 0.35rem;">Suggested Improvements</h4>
          <ul id="quality-improvements-list" style="font-size: 0.8rem; color: var(--text-secondary); padding-left: 1.25rem; margin: 0;">
            <li>Upload a resume for AI recommendations</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Extracted Information Preview Card (Initially Hidden) -->
    <div id="extracted-info-card" class="card" style="display: none; margin-bottom: 2rem; border-left: 4px solid var(--primary-color);">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem;">
        <div>
          <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary);">Information Detected From Your Resume</h3>
          <p style="font-size: 0.8rem; color: var(--text-muted);">Review detected skills, education, and links. Accept to update your Student Profile automatically.</p>
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <button id="accept-all-analysis-btn" class="btn btn-primary" style="font-size: 0.8rem;">✓ Accept & Update Profile</button>
          <button id="dismiss-analysis-btn" class="btn btn-outline" style="font-size: 0.8rem;">Ignore</button>
        </div>
      </div>

      <div id="extracted-fields-container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">
        <!-- Dynamic Extracted Fields -->
      </div>
    </div>
  `;
}

export function initResumeListeners() {
  const fileInput = document.getElementById("resume-file-input");
  const browseBtn = document.getElementById("resume-browse-btn");
  const dropZone = document.getElementById("resume-drop-zone");

  if (browseBtn && fileInput) {
    browseBtn.onclick = (e) => {
      e.stopPropagation();
      fileInput.click();
    };
  }

  if (dropZone) {
    dropZone.onclick = () => fileInput.click();
    dropZone.ondragover = (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--primary-color)";
    };
    dropZone.ondragleave = (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--border-hover)";
    };
    dropZone.ondrop = (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--border-hover)";
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        uploadResumeFile(e.dataTransfer.files[0]);
      }
    };
  }

  if (fileInput) {
    fileInput.onchange = (e) => {
      if (e.target.files && e.target.files.length > 0) {
        uploadResumeFile(e.target.files[0]);
      }
    };
  }

  loadResumeData();
}

async function uploadResumeFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    showToast("Uploading & analyzing resume text...", "info");
    const res = await api.post("/resumes/upload", formData, false);
    showToast("Resume uploaded & analyzed successfully!");
    await loadResumeData(res.id);
  } catch (err) {
    showToast(err.message || "Failed to upload resume.", "danger");
  }
}

async function loadResumeData(activeId = null) {
  try {
    const resumes = await api.get("/resumes");
    if (!resumes || resumes.length === 0) return;

    const activeResume = activeId ? resumes.find(r => r.id === activeId) || resumes[0] : resumes[0];

    document.getElementById("resume-uploaded-date").textContent = `Uploaded: ${new Date(activeResume.created_at).toLocaleDateString()}`;
    document.getElementById("resume-status-badge").textContent = activeResume.is_current ? "Active Resume" : "Previous Version";
    document.getElementById("resume-status-badge").className = activeResume.is_current ? "badge-status badge-success" : "badge-status badge-muted";

    document.getElementById("resume-file-name").textContent = activeResume.file_name;
    document.getElementById("resume-file-size").textContent = `${(activeResume.file_size_bytes / 1024).toFixed(1)} KB`;

    const viewBtn = document.getElementById("resume-view-btn");
    viewBtn.style.display = "inline-flex";
    viewBtn.href = activeResume.file_url;

    // Quality Score
    document.getElementById("quality-score-badge").textContent = `${activeResume.quality_score}/100`;
    const strengthsList = document.getElementById("quality-strengths-list");
    const improvementsList = document.getElementById("quality-improvements-list");

    if (activeResume.strengths && activeResume.strengths.length > 0) {
      strengthsList.innerHTML = activeResume.strengths.map(s => `<li>${s}</li>`).join("");
    } else {
      strengthsList.innerHTML = `<li>✓ Standard formatting</li>`;
    }

    if (activeResume.improvements && activeResume.improvements.length > 0) {
      improvementsList.innerHTML = activeResume.improvements.map(i => `<li>${i}</li>`).join("");
    } else {
      improvementsList.innerHTML = `<li>✓ Great resume completeness!</li>`;
    }

    // Load analysis if available
    loadResumeAnalysis(activeResume.id);

  } catch (err) {
    console.warn("Failed to load resume list:", err);
  }
}

async function loadResumeAnalysis(resumeId) {
  try {
    const analysis = await api.get(`/resumes/${resumeId}/analysis`);
    if (!analysis || !analysis.parsed_data) return;

    const data = analysis.parsed_data;
    const card = document.getElementById("extracted-info-card");
    const container = document.getElementById("extracted-fields-container");
    card.style.display = "block";

    container.innerHTML = `
      <div style="background: var(--bg-card); border: 1px solid var(--border-color); padding: 0.875rem; border-radius: var(--radius-md);">
        <div style="font-size: 0.75rem; color: var(--text-muted);">NAME DETECTED</div>
        <div style="font-weight: 700; font-size: 0.9rem; color: var(--text-primary); margin-top: 0.2rem;">${data.full_name || 'Not detected'}</div>
      </div>
      <div style="background: var(--bg-card); border: 1px solid var(--border-color); padding: 0.875rem; border-radius: var(--radius-md);">
        <div style="font-size: 0.75rem; color: var(--text-muted);">CONTACT DETECTED</div>
        <div style="font-weight: 600; font-size: 0.85rem; color: var(--text-primary); margin-top: 0.2rem;">${data.email || '—'} | ${data.phone || '—'}</div>
      </div>
      <div style="background: var(--bg-card); border: 1px solid var(--border-color); padding: 0.875rem; border-radius: var(--radius-md);">
        <div style="font-size: 0.75rem; color: var(--text-muted);">SKILLS DETECTED (${(data.skills || []).length})</div>
        <div style="font-weight: 600; font-size: 0.825rem; color: var(--primary-color); margin-top: 0.2rem;">${(data.skills || []).join(", ") || 'None detected'}</div>
      </div>
      <div style="background: var(--bg-card); border: 1px solid var(--border-color); padding: 0.875rem; border-radius: var(--radius-md);">
        <div style="font-size: 0.75rem; color: var(--text-muted);">EDUCATION DETECTED</div>
        <div style="font-weight: 600; font-size: 0.85rem; color: var(--text-primary); margin-top: 0.2rem;">${(data.education || []).join(", ") || 'None detected'}</div>
      </div>
    `;

    document.getElementById("accept-all-analysis-btn").onclick = async () => {
      try {
        await api.post(`/resumes/${resumeId}/apply-analysis`, {
          accept_fields: ["phone", "skills", "education", "linkedin_url", "github_url"]
        });
        showToast("Extracted information accepted & applied to profile!");
        card.style.display = "none";
      } catch (err) {
        showToast(err.message || "Failed to apply analysis.", "danger");
      }
    };

    document.getElementById("dismiss-analysis-btn").onclick = () => {
      card.style.display = "none";
    };

  } catch (err) {
    // Analysis optional
  }
}
