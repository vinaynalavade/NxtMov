import { api, getAuthenticatedFileUrl } from "../api.js";
import { showToast } from "../components.js";
import { getIcon } from "../icons.js";

export function renderResume() {
  return `
    <div class="view-header">
      <div>
        <h1 class="view-title">Resume & ATS Intelligence Center</h1>
        <p class="view-subtitle">Upload your resume to calculate your domain-adaptive NxtMov ATS Score, verify multi-entry qualifications, and inspect categorized skills.</p>
      </div>
    </div>

    <!-- Upload Card -->
    <div class="card" style="margin-bottom: 2rem;">
      <div id="resume-drop-zone" style="border: 2px dashed var(--border-hover); border-radius: var(--radius-xl); padding: 2.5rem 1.5rem; text-align: center; background-color: var(--bg-secondary); cursor: pointer; transition: border-color 150ms ease;">
        <div style="margin-bottom: 0.75rem; color: var(--primary-color);">
          ${getIcon("upload", "upload-drop-icon", 36)}
        </div>
        <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.25rem;">Upload or Replace Your Resume</h3>
        <p style="color: var(--text-muted); font-size: 0.825rem; max-width: 480px; margin: 0 auto 1.25rem auto;">
          Supports <strong>.pdf</strong>, <strong>.docx</strong>, and <strong>.txt</strong>. NxtMov analyzes career domain alignment, keyword density, structured education entries, and ATS readability.
        </p>
        <input type="file" id="resume-file-input" accept=".pdf,.docx,.txt" style="display: none;" />
        <button id="resume-browse-btn" class="btn btn-primary btn-lg" style="gap: 0.5rem;">
          ${getIcon("file-text", "", 18)} Browse Resume File
        </button>
      </div>
    </div>

    <!-- Active Resume Card & ATS Score Container -->
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
          <div style="color: var(--primary-color);">
            ${getIcon("resume", "", 28)}
          </div>
          <div style="flex: 1; overflow: hidden;">
            <div id="resume-file-name" style="font-weight: 700; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">-</div>
            <div id="resume-file-size" style="font-size: 0.75rem; color: var(--text-muted);">-</div>
          </div>
        </div>

        <!-- Career Domain Badge in Current Card -->
        <div id="card-domain-info" style="margin-bottom: 1.25rem; display: none;">
          <div style="font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; margin-bottom: 0.25rem;">Detected Career Domain</div>
          <div id="card-domain-title" style="font-size: 0.95rem; font-weight: 700; color: var(--primary-color);">-</div>
          <div id="card-roles-list" style="display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.35rem;"></div>
        </div>

        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
          <a id="resume-view-btn" href="#" target="_blank" class="btn btn-outline" style="font-size: 0.8rem; display: none; gap: 0.4rem;">
            ${getIcon("eye", "", 16)} View Resume
          </a>
        </div>
      </div>

      <!-- NxtMov ATS Score Card -->
      <div id="resume-quality-card" class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <div>
            <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary);">NxtMov ATS Score</h3>
            <p id="ats-score-domain-sub" style="font-size: 0.75rem; color: var(--text-muted); margin: 0;">Domain-adaptive deterministic analysis</p>
          </div>
          <div id="quality-score-badge" style="font-size: 1.6rem; font-weight: 800; color: var(--primary-color);">--/100</div>
        </div>

        <!-- Domain Explanation Banner -->
        <div id="ats-domain-explanation-box" style="display: none; background: var(--bg-secondary); border-left: 3px solid var(--primary-color); padding: 0.65rem 0.85rem; border-radius: var(--radius-md); font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 1rem;">
        </div>

        <!-- Score Breakdown Meters -->
        <div id="ats-score-breakdown" style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem 1rem; margin-bottom: 1.25rem; font-size: 0.775rem;">
          <div>
            <div style="display: flex; justify-content: space-between; color: var(--text-secondary); margin-bottom: 0.15rem;">
              <span>Contact Details</span> <strong id="score-bd-contact">--/10</strong>
            </div>
            <div style="height: 4px; background: var(--border-color); border-radius: 2px; overflow: hidden;">
              <div id="bar-bd-contact" style="width: 0%; height: 100%; background: var(--primary-color); transition: width 400ms;"></div>
            </div>
          </div>
          <div>
            <div style="display: flex; justify-content: space-between; color: var(--text-secondary); margin-bottom: 0.15rem;">
              <span>Structure</span> <strong id="score-bd-struct">--/15</strong>
            </div>
            <div style="height: 4px; background: var(--border-color); border-radius: 2px; overflow: hidden;">
              <div id="bar-bd-struct" style="width: 0%; height: 100%; background: var(--primary-color); transition: width 400ms;"></div>
            </div>
          </div>
          <div>
            <div style="display: flex; justify-content: space-between; color: var(--text-secondary); margin-bottom: 0.15rem;">
              <span>Keywords</span> <strong id="score-bd-kw">--/20</strong>
            </div>
            <div style="height: 4px; background: var(--border-color); border-radius: 2px; overflow: hidden;">
              <div id="bar-bd-kw" style="width: 0%; height: 100%; background: var(--primary-color); transition: width 400ms;"></div>
            </div>
          </div>
          <div>
            <div style="display: flex; justify-content: space-between; color: var(--text-secondary); margin-bottom: 0.15rem;">
              <span>Experience & Impact</span> <strong id="score-bd-exp">--/20</strong>
            </div>
            <div style="height: 4px; background: var(--border-color); border-radius: 2px; overflow: hidden;">
              <div id="bar-bd-exp" style="width: 0%; height: 100%; background: var(--primary-color); transition: width 400ms;"></div>
            </div>
          </div>
          <div>
            <div style="display: flex; justify-content: space-between; color: var(--text-secondary); margin-bottom: 0.15rem;">
              <span>Skills Diversity</span> <strong id="score-bd-skills">--/15</strong>
            </div>
            <div style="height: 4px; background: var(--border-color); border-radius: 2px; overflow: hidden;">
              <div id="bar-bd-skills" style="width: 0%; height: 100%; background: var(--primary-color); transition: width 400ms;"></div>
            </div>
          </div>
          <div>
            <div style="display: flex; justify-content: space-between; color: var(--text-secondary); margin-bottom: 0.15rem;">
              <span>Education</span> <strong id="score-bd-edu">--/10</strong>
            </div>
            <div style="height: 4px; background: var(--border-color); border-radius: 2px; overflow: hidden;">
              <div id="bar-bd-edu" style="width: 0%; height: 100%; background: var(--primary-color); transition: width 400ms;"></div>
            </div>
          </div>
        </div>

        <div style="margin-bottom: 1rem;">
          <h4 style="font-size: 0.85rem; font-weight: 700; color: var(--accent-color); margin-bottom: 0.35rem; display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("award", "", 16)} Strengths
          </h4>
          <ul id="quality-strengths-list" style="font-size: 0.8rem; color: var(--text-secondary); padding-left: 1.25rem; margin: 0; display: flex; flex-direction: column; gap: 0.25rem;">
            <li>Upload a resume to calculate ATS ranking</li>
          </ul>
        </div>

        <div style="margin-bottom: 1rem;">
          <h4 style="font-size: 0.85rem; font-weight: 700; color: var(--warning-color); margin-bottom: 0.35rem; display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("alert", "", 16)} Improvement Areas
          </h4>
          <ul id="quality-improvements-list" style="font-size: 0.8rem; color: var(--text-secondary); padding-left: 1.25rem; margin: 0; display: flex; flex-direction: column; gap: 0.25rem;">
            <li>Upload a resume for tailored recommendations</li>
          </ul>
        </div>

        <!-- Warnings Section -->
        <div id="quality-warnings-container" style="display: none;">
          <h4 style="font-size: 0.85rem; font-weight: 700; color: var(--danger-color); margin-bottom: 0.35rem; display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("alert-circle", "", 16)} Warnings & Weak Phrases
          </h4>
          <ul id="quality-warnings-list" style="font-size: 0.8rem; color: var(--text-secondary); padding-left: 1.25rem; margin: 0; display: flex; flex-direction: column; gap: 0.25rem;">
          </ul>
        </div>
      </div>
    </div>

    <!-- Extracted Information Preview Card (Initially Hidden) -->
    <div id="extracted-info-card" class="card" style="display: none; margin-bottom: 2rem; border-left: 4px solid var(--primary-color);">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem; flex-wrap: wrap; gap: 0.75rem;">
        <div>
          <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary);">Information Detected From Your Resume</h3>
          <p style="font-size: 0.8rem; color: var(--text-muted); margin: 0;">Review detected career domain, multi-degree education records, and categorized skills. Accept to update your profile.</p>
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <button id="accept-all-analysis-btn" class="btn btn-primary" style="font-size: 0.8rem; gap: 0.4rem;">
            ${getIcon("check", "", 16)} Accept & Update Profile
          </button>
          <button id="dismiss-analysis-btn" class="btn btn-ghost" style="font-size: 0.8rem;">Dismiss</button>
        </div>
      </div>

      <div id="extracted-fields-container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem;">
      </div>
    </div>
  `;
}

export function initResumeEvents() {
  const dropZone = document.getElementById("resume-drop-zone");
  const fileInput = document.getElementById("resume-file-input");
  const browseBtn = document.getElementById("resume-browse-btn");

  if (browseBtn && fileInput) {
    browseBtn.onclick = (e) => {
      e.stopPropagation();
      fileInput.click();
    };
  }

  if (dropZone && fileInput) {
    dropZone.onclick = () => fileInput.click();

    dropZone.ondragover = (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--primary-color)";
      dropZone.style.backgroundColor = "var(--bg-card)";
    };

    dropZone.ondragleave = () => {
      dropZone.style.borderColor = "var(--border-hover)";
      dropZone.style.backgroundColor = "var(--bg-secondary)";
    };

    dropZone.ondrop = (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--border-hover)";
      dropZone.style.backgroundColor = "var(--bg-secondary)";
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
    showToast("Uploading & running ATS intelligence analysis...", "info");
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

    // Authenticated View Resume File
    const viewBtn = document.getElementById("resume-view-btn");
    viewBtn.style.display = "inline-flex";
    const fileUrl = getAuthenticatedFileUrl(activeResume.file_url || `/api/v1/resumes/${activeResume.id}/file`);
    viewBtn.href = fileUrl;
    viewBtn.onclick = (e) => {
      e.preventDefault();
      window.open(fileUrl, "_blank");
    };

    // Detected Career Domain & Roles
    if (activeResume.career_domain) {
      const domainBox = document.getElementById("card-domain-info");
      const domainTitle = document.getElementById("card-domain-title");
      const rolesList = document.getElementById("card-roles-list");
      if (domainBox && domainTitle && rolesList) {
        domainBox.style.display = "block";
        domainTitle.textContent = activeResume.career_domain;
        if (activeResume.likely_roles && activeResume.likely_roles.length > 0) {
          rolesList.innerHTML = activeResume.likely_roles.map(r => `<span class="badge" style="background: var(--bg-secondary); color: var(--primary-color); border: 1px solid var(--border-color); font-size: 0.725rem;">${r}</span>`).join("");
        } else {
          rolesList.innerHTML = "";
        }
      }

      const domainSub = document.getElementById("ats-score-domain-sub");
      if (domainSub) {
        domainSub.textContent = `Adaptive analysis for ${activeResume.career_domain}`;
      }

      const explBox = document.getElementById("ats-domain-explanation-box");
      if (explBox && activeResume.domain_explanation) {
        explBox.style.display = "block";
        explBox.innerHTML = `<strong>Domain Insights:</strong> ${activeResume.domain_explanation}`;
      }
    }

    // ATS Score
    const scoreVal = activeResume.ats_score || activeResume.quality_score || 0;
    document.getElementById("quality-score-badge").textContent = `${scoreVal}/100`;
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

    // Warnings
    const warnContainer = document.getElementById("quality-warnings-container");
    const warnList = document.getElementById("quality-warnings-list");
    if (warnContainer && warnList) {
      if (activeResume.warnings && activeResume.warnings.length > 0) {
        warnContainer.style.display = "block";
        warnList.innerHTML = activeResume.warnings.map(w => `<li>${w}</li>`).join("");
      } else {
        warnContainer.style.display = "none";
      }
    }

    // Score Breakdown Bars
    if (activeResume.score_breakdown) {
      const bd = activeResume.score_breakdown;
      setBreakdown("contact", bd.contact_info || 0, 10);
      setBreakdown("struct", bd.structure || 0, 15);
      setBreakdown("kw", bd.keyword_coverage || 0, 20);
      setBreakdown("exp", bd.experience_projects || 0, 20);
      setBreakdown("skills", bd.skills_diversity || 0, 15);
      setBreakdown("edu", bd.education || 0, 10);
    }

    // Load detailed analysis
    loadResumeAnalysis(activeResume.id);

  } catch (err) {
    console.warn("Failed to load resume list:", err);
  }
}

function setBreakdown(idKey, score, max) {
  const textEl = document.getElementById(`score-bd-${idKey}`);
  const barEl = document.getElementById(`bar-bd-${idKey}`);
  if (textEl) textEl.textContent = `${score}/${max}`;
  if (barEl) barEl.style.width = `${Math.min(100, (score / max) * 100)}%`;
}

async function loadResumeAnalysis(resumeId) {
  try {
    const analysis = await api.get(`/resumes/${resumeId}/analysis`);
    if (!analysis || !analysis.parsed_data) return;

    const data = analysis.parsed_data;
    const card = document.getElementById("extracted-info-card");
    const container = document.getElementById("extracted-fields-container");
    card.style.display = "block";

    // Format Education Entries
    let eduHtml = "";
    if (data.education_entries && data.education_entries.length > 0) {
      eduHtml = data.education_entries.map(e => `
        <div style="background: var(--bg-secondary); border-left: 3px solid var(--primary-color); padding: 0.65rem 0.85rem; border-radius: var(--radius-md); margin-bottom: 0.5rem;">
          <div style="font-weight: 700; font-size: 0.875rem; color: var(--text-primary);">${e.degree}${e.specialization ? ` — ${e.specialization}` : ''}</div>
          <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.15rem;">${e.institution || 'Academic Institution'}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; display: flex; gap: 1rem;">
            ${e.year ? `<span><strong>Year:</strong> ${e.year}</span>` : ''}
            ${e.score ? `<span><strong>Score:</strong> ${e.score}</span>` : ''}
          </div>
        </div>
      `).join("");
    } else if (data.education && data.education.length > 0) {
      eduHtml = `<div style="font-size: 0.85rem; color: var(--text-primary);">${data.education.join("<br>")}</div>`;
    } else {
      eduHtml = `<div style="font-size: 0.8rem; color: var(--text-muted);">No education records detected</div>`;
    }

    // Format Categorized Skills
    let skillsHtml = "";
    if (data.categorized_skills && Object.keys(data.categorized_skills).length > 0) {
      skillsHtml = Object.entries(data.categorized_skills).map(([catName, skillList]) => `
        <div style="margin-bottom: 0.6rem;">
          <div style="font-size: 0.675rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.25rem; letter-spacing: 0.05em;">${catName}</div>
          <div style="display: flex; flex-wrap: wrap; gap: 0.35rem;">
            ${skillList.map(s => `<span class="badge" style="background: var(--bg-secondary); color: var(--primary-color); border: 1px solid var(--border-color); font-size: 0.75rem; padding: 0.15rem 0.45rem; border-radius: 6px;">${s}</span>`).join("")}
          </div>
        </div>
      `).join("");
    } else if (data.skills && data.skills.length > 0) {
      skillsHtml = `<div style="display: flex; flex-wrap: wrap; gap: 0.35rem;">${data.skills.map(s => `<span class="badge" style="background: var(--bg-secondary); color: var(--primary-color); font-size: 0.75rem; padding: 0.15rem 0.45rem; border-radius: 6px;">${s}</span>`).join("")}</div>`;
    } else {
      skillsHtml = `<span style="font-size: 0.8rem; color: var(--text-muted);">None detected</span>`;
    }

    const links = [];
    if (data.linkedin_url) links.push(`<a href="${data.linkedin_url}" target="_blank" style="color: var(--primary-color); font-weight: 600;">LinkedIn Profile</a>`);
    if (data.github_url) links.push(`<a href="${data.github_url}" target="_blank" style="color: var(--primary-color); font-weight: 600;">GitHub Profile</a>`);

    let linksHtml = "";
    if (links.length > 0) {
      linksHtml = `
        <div style="background: var(--bg-card); border: 1px solid var(--border-color); padding: 0.875rem; border-radius: var(--radius-md); grid-column: 1 / -1;">
          <div style="font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; margin-bottom: 0.35rem;">ONLINE PROFILES & PORTFOLIO</div>
          <div style="display: flex; gap: 1rem; align-items: center; font-size: 0.85rem;">${links.join(" &bull; ")}</div>
        </div>
      `;
    }

    container.innerHTML = `
      <div style="background: var(--bg-card); border: 1px solid var(--border-color); padding: 0.875rem; border-radius: var(--radius-md);">
        <div style="font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; margin-bottom: 0.35rem;">CANDIDATE IDENTITY</div>
        <div style="font-weight: 700; font-size: 0.95rem; color: var(--text-primary);">${data.full_name || 'Not detected'}</div>
        <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">${data.email || '—'} &bull; ${data.phone || '—'}</div>
      </div>

      <div style="background: var(--bg-card); border: 1px solid var(--border-color); padding: 0.875rem; border-radius: var(--radius-md);">
        <div style="font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; margin-bottom: 0.35rem;">CAREER DOMAIN DETECTED</div>
        <div style="font-weight: 700; font-size: 0.95rem; color: var(--primary-color);">${data.career_domain || 'General Technical Profile'}</div>
        <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">
          ${(data.likely_roles || []).join(" • ") || 'Technical Associate'}
        </div>
      </div>

      <div style="background: var(--bg-card); border: 1px solid var(--border-color); padding: 0.875rem; border-radius: var(--radius-md);">
        <div style="font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; margin-bottom: 0.5rem;">EDUCATION DETECTED (${(data.education_entries || []).length || (data.education || []).length})</div>
        ${eduHtml}
      </div>

      <div style="background: var(--bg-card); border: 1px solid var(--border-color); padding: 0.875rem; border-radius: var(--radius-md);">
        <div style="font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; margin-bottom: 0.5rem;">CATEGORIZED SKILLS DETECTED (${data.skills ? data.skills.length : 0})</div>
        ${skillsHtml}
      </div>

      ${linksHtml}
    `;

    document.getElementById("accept-all-analysis-btn").onclick = async () => {
      try {
        await api.post(`/resumes/${resumeId}/apply-analysis`, {
          accept_fields: ["name", "email", "phone", "skills", "education", "linkedin_url", "github_url"]
        });
        showToast("Profile successfully updated with detected resume data!");
        card.style.display = "none";
      } catch (err) {
        showToast(err.message || "Failed to apply analysis.", "danger");
      }
    };

    document.getElementById("dismiss-analysis-btn").onclick = () => {
      card.style.display = "none";
    };

  } catch (err) {
    console.warn("Failed to load resume analysis:", err);
  }
}
