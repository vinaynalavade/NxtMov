import { api, getAuthenticatedFileUrl } from "../api.js";
import { showToast, createModal, validateFullName, validateEmail, validatePhone, validateUrl } from "../components.js";
import { store } from "../store.js";
import { getIcon } from "../icons.js";

export function renderProfile() {
  return `
    <div class="view-header">
      <div>
        <h1 class="view-title">Talent Profile & Settings</h1>
        <p class="view-subtitle">Manage your personal details, career preferences, multi-degree education records, technical skills, and account security.</p>
      </div>
    </div>

    <!-- Top Card: Profile Completeness Score & Hero Avatar -->
    <div class="card" style="margin-bottom: 1.5rem; background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%);">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1.5rem;">
        <div style="display: flex; align-items: center; gap: 1.5rem; flex-wrap: wrap;">
          <div style="position: relative; width: 80px; height: 80px; flex-shrink: 0;">
            <div id="profile-avatar-container" style="width: 80px; height: 80px; border-radius: 50%; overflow: hidden; border: 3px solid var(--primary-color); background: linear-gradient(135deg, var(--primary-color) 0%, #3B82F6 100%); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 1.5rem; font-weight: 700; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);">
              <img id="profile-avatar-img" src="./favicon.svg" alt="Avatar" style="width: 100%; height: 100%; object-fit: cover; display: none;" />
              <span id="profile-avatar-initials">US</span>
            </div>
            <label for="avatar-upload-input" style="position: absolute; bottom: -2px; right: -2px; background: var(--primary-color); color: #fff; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 2px 6px rgba(0,0,0,0.25); border: 2px solid var(--bg-card);" title="Upload Profile Picture">
              ${getIcon("camera", "", 14)}
            </label>
            <input type="file" id="avatar-upload-input" accept="image/png, image/jpeg, image/webp, image/svg+xml" style="display: none;" />
          </div>

          <div>
            <div style="display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;">
              <h3 id="profile-header-name" style="font-size: 1.3rem; font-weight: 700; color: var(--text-primary); margin: 0;">-</h3>
              <button id="btn-remove-avatar" class="btn btn-ghost btn-sm" style="font-size: 0.75rem; color: var(--text-muted); display: none; padding: 0.2rem 0.5rem; gap: 0.25rem;" title="Remove profile picture">
                ${getIcon("trash", "", 12)} Remove Picture
              </button>
            </div>
            <p id="profile-header-headline" style="font-size: 0.85rem; color: var(--text-secondary); margin: 0.2rem 0 0.4rem 0;">-</p>
            <div id="profile-header-contact" style="font-size: 0.8rem; color: var(--text-muted); display: flex; gap: 1rem; flex-wrap: wrap; align-items: center;"></div>
          </div>
        </div>

        <div style="min-width: 260px; flex: 1; max-width: 380px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
            <span style="font-size: 0.8rem; font-weight: 700; color: var(--text-primary);">Profile Completeness</span>
            <span id="profile-completeness-text" style="font-size: 0.85rem; font-weight: 800; color: var(--primary-color);">0%</span>
          </div>
          <div style="width: 100%; height: 10px; background-color: var(--border-color); border-radius: 999px; overflow: hidden;">
            <div id="profile-completeness-bar" style="width: 0%; height: 100%; background: linear-gradient(90deg, var(--primary-color), #3B82F6); transition: width 300ms ease;"></div>
          </div>
          <div id="profile-missing-items" style="font-size: 0.75rem; color: var(--warning-color); margin-top: 0.45rem;"></div>
        </div>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="tabs-header" style="display: flex; gap: 0.5rem; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; flex-wrap: wrap;">
      <button class="btn btn-outline profile-tab-btn active" data-tab="tab-personal" style="gap: 0.4rem;">
        ${getIcon("user", "", 15)} Personal & Location
      </button>
      <button class="btn btn-outline profile-tab-btn" data-tab="tab-professional" style="gap: 0.4rem;">
        ${getIcon("target", "", 15)} Career Goals & Preferences
      </button>
      <button class="btn btn-outline profile-tab-btn" data-tab="tab-education" style="gap: 0.4rem;">
        ${getIcon("graduation-cap", "", 15)} Education & Skills
      </button>
      <button class="btn btn-outline profile-tab-btn" data-tab="tab-links" style="gap: 0.4rem;">
        ${getIcon("link", "", 15)} Projects & Profiles
      </button>
      <button class="btn btn-outline profile-tab-btn" data-tab="tab-settings" style="gap: 0.4rem;">
        ${getIcon("settings", "", 15)} Identity & Security
      </button>
    </div>

    <!-- Tab 1: Personal Information -->
    <div id="tab-personal" class="profile-tab-content card">
      <h3 style="font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem; color: var(--text-primary);">Location & Contact Address</h3>
      <form id="profile-personal-form" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">
        <div class="form-group">
          <label>City</label>
          <input type="text" id="prof-city" class="form-control" placeholder="e.g. Pune, Mumbai, Bengaluru" />
        </div>
        <div class="form-group">
          <label>State</label>
          <input type="text" id="prof-state" class="form-control" placeholder="e.g. Maharashtra, Karnataka" />
        </div>
        <div class="form-group">
          <label>Country</label>
          <input type="text" id="prof-country" class="form-control" value="India" />
        </div>
        <div style="grid-column: 1 / -1; display: flex; justify-content: flex-end;">
          <button type="submit" id="btn-save-personal" class="btn btn-primary" style="gap: 0.4rem;">
            ${getIcon("check", "", 16)} Save Location Info
          </button>
        </div>
      </form>
    </div>

    <!-- Tab 2: Professional Information -->
    <div id="tab-professional" class="profile-tab-content card" style="display: none;">
      <h3 style="font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem; color: var(--text-primary);">Career Goals & Preferences</h3>
      <form id="profile-professional-form" style="display: flex; flex-direction: column; gap: 1rem;">
        <div class="form-group">
          <label>Professional Headline / Tagline</label>
          <input type="text" id="prof-headline" class="form-control" placeholder="e.g. Full Stack Developer | Python, FastAPI, React" />
        </div>
        <div class="form-group">
          <label>Career Objective / Summary</label>
          <textarea id="prof-objective" class="form-control" rows="3" placeholder="Detail your professional experience, technical achievements, and target opportunities..."></textarea>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">
          <div class="form-group">
            <label>Preferred Roles (Comma separated)</label>
            <input type="text" id="prof-pref-roles" class="form-control" placeholder="Full Stack Developer, Backend Engineer, QA Lead" />
          </div>
          <div class="form-group">
            <label>Preferred Locations (Comma separated)</label>
            <input type="text" id="prof-pref-locations" class="form-control" placeholder="Pune, Mumbai, Bengaluru, Remote" />
          </div>
          <div class="form-group">
            <label>Employment Preference</label>
            <select id="prof-pref-emp" class="form-control">
              <option value="FULL_TIME">Full Time</option>
              <option value="CONTRACT">Contract</option>
              <option value="PART_TIME">Part Time</option>
              <option value="INTERNSHIP">Internship</option>
            </select>
          </div>
          <div class="form-group">
            <label>Expected Annual Salary (LPA / INR)</label>
            <input type="number" step="0.5" id="prof-expected-salary" min="0" max="1000" class="form-control" placeholder="e.g. 8.5" />
          </div>
          <div class="form-group">
            <label>Notice Period (Days)</label>
            <input type="number" id="prof-notice-period" min="0" max="365" class="form-control" placeholder="e.g. 15, 30, 0 for Immediate" />
          </div>
        </div>
        <div style="display: flex; justify-content: flex-end;">
          <button type="submit" id="btn-save-professional" class="btn btn-primary" style="gap: 0.4rem;">
            ${getIcon("check", "", 16)} Save Professional Info
          </button>
        </div>
      </form>
    </div>

    <!-- Tab 3: Education & Skills -->
    <div id="tab-education" class="profile-tab-content card" style="display: none;">
      <h3 style="font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem; color: var(--text-primary);">Academic Qualifications & Technical Skills</h3>
      <form id="profile-edu-skills-form" style="display: flex; flex-direction: column; gap: 1.25rem;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">
          <div class="form-group">
            <label>Highest Qualification</label>
            <input type="text" id="prof-highest-qual" class="form-control" placeholder="e.g. Bachelor of Technology (B.Tech)" />
          </div>
          <div class="form-group">
            <label>Degree / Specialization</label>
            <input type="text" id="prof-degree" class="form-control" placeholder="e.g. Computer Science & Engineering" />
          </div>
          <div class="form-group">
            <label>College / University / Board</label>
            <input type="text" id="prof-college" class="form-control" placeholder="e.g. DBATU University – Fabtech Campus" />
          </div>
          <div class="form-group">
            <label>Graduation Year</label>
            <input type="number" id="prof-grad-year" min="1960" max="2035" class="form-control" placeholder="e.g. 2024" />
          </div>
          <div class="form-group">
            <label>CGPA / Percentage</label>
            <input type="text" id="prof-cgpa" class="form-control" placeholder="e.g. CGPA 7.98 or 84.00%" />
          </div>
        </div>

        <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary); border-top: 1px solid var(--border-color); padding-top: 1rem; margin: 0;">Multi-Domain Technical Skills</h4>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">
          <div class="form-group">
            <label>Programming Languages</label>
            <input type="text" id="prof-prog-langs" class="form-control" placeholder="Python, Java, JavaScript, TypeScript, SQL" />
          </div>
          <div class="form-group">
            <label>Frontend & Backend Frameworks</label>
            <input type="text" id="prof-frameworks" class="form-control" placeholder="React, Node.js, FastAPI, Django, Spring Boot" />
          </div>
          <div class="form-group">
            <label>Testing, QA & Automation Tools</label>
            <input type="text" id="prof-testing-tools" class="form-control" placeholder="Selenium, Postman, Pytest, Cypress, JUnit" />
          </div>
          <div class="form-group">
            <label>Databases, Cloud & DevOps</label>
            <input type="text" id="prof-databases" class="form-control" placeholder="PostgreSQL, MongoDB, Docker, AWS, Git, CI/CD" />
          </div>
        </div>

        <div style="display: flex; justify-content: flex-end;">
          <button type="submit" id="btn-save-education" class="btn btn-primary" style="gap: 0.4rem;">
            ${getIcon("check", "", 16)} Save Education & Skills
          </button>
        </div>
      </form>
    </div>

    <!-- Tab 4: Projects & Links -->
    <div id="tab-links" class="profile-tab-content card" style="display: none;">
      <h3 style="font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem; color: var(--text-primary);">Online Profiles & Portfolio Links</h3>
      <form id="profile-links-form" style="display: flex; flex-direction: column; gap: 1rem;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">
          <div class="form-group">
            <label>LinkedIn Profile URL</label>
            <input type="url" id="prof-linkedin" class="form-control" placeholder="https://linkedin.com/in/username" />
          </div>
          <div class="form-group">
            <label>GitHub Profile URL</label>
            <input type="url" id="prof-github" class="form-control" placeholder="https://github.com/username" />
          </div>
          <div class="form-group">
            <label>Portfolio / Personal Website</label>
            <input type="url" id="prof-portfolio" class="form-control" placeholder="https://yourportfolio.com" />
          </div>
        </div>
        <div class="form-group">
          <label>Projects Summary (Optional)</label>
          <textarea id="prof-projects" class="form-control" rows="3" placeholder="Key projects, system architectures built, or open-source contributions..."></textarea>
        </div>
        <div style="display: flex; justify-content: flex-end;">
          <button type="submit" id="btn-save-links" class="btn btn-primary" style="gap: 0.4rem;">
            ${getIcon("check", "", 16)} Save Links & Projects
          </button>
        </div>
      </form>
    </div>

    <!-- Tab 5: Settings & Verification Security -->
    <div id="tab-settings" class="profile-tab-content card" style="display: none;">
      <h3 style="font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem; color: var(--text-primary);">Identity Verification & Account Security</h3>
      
      <!-- Identity Verification Cards -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
        <!-- Email Verification Box -->
        <div style="background: var(--bg-secondary); padding: 1rem; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <strong style="font-size: 0.85rem; color: var(--text-primary);">Email Verification</strong>
            <span id="badge-email-status" class="badge-status badge-muted">Checking...</span>
          </div>
          <p id="label-email-val" style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.75rem;">-</p>
          <button id="btn-verify-email-action" class="btn btn-outline btn-sm" style="display: none; gap: 0.35rem;">
            ${getIcon("mail", "", 14)} Send Verification Link
          </button>
        </div>

        <!-- Phone Verification Box -->
        <div style="background: var(--bg-secondary); padding: 1rem; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <strong style="font-size: 0.85rem; color: var(--text-primary);">Mobile OTP Verification</strong>
            <span id="badge-phone-status" class="badge-status badge-muted">Checking...</span>
          </div>
          <p id="label-phone-val" style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.75rem;">-</p>
          <button id="btn-verify-phone-action" class="btn btn-outline btn-sm" style="display: none; gap: 0.35rem;">
            ${getIcon("phone", "", 14)} Verify Mobile with OTP
          </button>
        </div>
      </div>

      <form id="profile-settings-form" style="display: flex; flex-direction: column; gap: 1rem; max-width: 480px;">
        <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary); margin: 0;">Account Profile</h4>
        <div class="form-group">
          <label>Full Name *</label>
          <input type="text" id="settings-name" required class="form-control" />
          <div id="err-settings-name" style="font-size: 0.75rem; color: var(--danger-color); display: none; margin-top: 0.2rem;"></div>
        </div>
        <div class="form-group">
          <label>Email Address *</label>
          <input type="email" id="settings-email" required class="form-control" />
          <div id="err-settings-email" style="font-size: 0.75rem; color: var(--danger-color); display: none; margin-top: 0.2rem;"></div>
        </div>
        <div class="form-group">
          <label>Mobile Number</label>
          <input type="text" id="settings-phone" class="form-control" placeholder="+91 9359345433" />
          <div id="err-settings-phone" style="font-size: 0.75rem; color: var(--danger-color); display: none; margin-top: 0.2rem;"></div>
        </div>

        <h4 style="font-size: 0.95rem; font-weight: 700; margin-top: 1rem; border-top: 1px solid var(--border-color); padding-top: 1rem; color: var(--text-primary);">Change Password</h4>
        <div class="form-group">
          <label>Current Password</label>
          <input type="password" id="settings-old-pass" class="form-control" placeholder="Leave empty to keep current password" />
        </div>
        <div class="form-group">
          <label>New Password</label>
          <input type="password" id="settings-new-pass" class="form-control" placeholder="Minimum 6 characters" />
        </div>

        <div style="display: flex; justify-content: flex-end;">
          <button type="submit" id="btn-save-settings" class="btn btn-primary" style="gap: 0.4rem;">
            ${getIcon("check", "", 16)} Update Account Credentials
          </button>
        </div>
      </form>
    </div>
  `;
}

export function initProfileEvents() {
  // Tabs Navigation
  const tabBtns = document.querySelectorAll(".profile-tab-btn");
  const tabContents = document.querySelectorAll(".profile-tab-content");

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.style.display = "none");
      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      const targetEl = document.getElementById(targetId);
      if (targetEl) targetEl.style.display = "block";
    });
  });

  // Avatar Upload & Removal
  const avatarInput = document.getElementById("avatar-upload-input");
  if (avatarInput) {
    avatarInput.addEventListener("change", async (e) => {
      if (e.target.files && e.target.files.length > 0) {
        const file = e.target.files[0];
        const formData = new FormData();
        formData.append("file", file);
        try {
          showToast("Uploading profile picture...", "info");
          const res = await api.post("/profile/avatar", formData, false);
          showToast("Profile picture updated!");
          loadProfileData();
        } catch (err) {
          showToast(err.message || "Failed to upload avatar.", "danger");
        }
      }
    });
  }

  const removeAvatarBtn = document.getElementById("btn-remove-avatar");
  if (removeAvatarBtn) {
    removeAvatarBtn.addEventListener("click", async () => {
      try {
        await api.delete("/profile/avatar");
        showToast("Profile picture removed.");
        loadProfileData();
      } catch (err) {
        showToast(err.message || "Failed to remove avatar.", "danger");
      }
    });
  }

  // Personal Form Submit
  document.getElementById("profile-personal-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const city = document.getElementById("prof-city").value.trim();
    const state = document.getElementById("prof-state").value.trim();
    const country = document.getElementById("prof-country").value.trim();

    try {
      await api.put("/profile", { city, state, country });
      showToast("Personal details saved successfully!");
      loadProfileData();
    } catch (err) {
      showToast(err.message || "Failed to save personal info.", "danger");
    }
  });

  // Professional Form Submit
  document.getElementById("profile-professional-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const headline = document.getElementById("prof-headline").value.trim();
    const career_objective = document.getElementById("prof-objective").value.trim();
    const preferred_roles = document.getElementById("prof-pref-roles").value.trim();
    const preferred_locations = document.getElementById("prof-pref-locations").value.trim();
    const employment_preference = document.getElementById("prof-pref-emp").value;
    const salaryVal = document.getElementById("prof-expected-salary").value;
    const noticeVal = document.getElementById("prof-notice-period").value;

    const payload = {
      headline,
      career_objective,
      preferred_roles,
      preferred_locations,
      employment_preference,
      expected_salary: salaryVal ? parseFloat(salaryVal) : null,
      notice_period_days: noticeVal ? parseInt(noticeVal) : null
    };

    try {
      await api.put("/profile", payload);
      showToast("Career goals and preferences saved!");
      loadProfileData();
    } catch (err) {
      showToast(err.message || "Failed to save professional info.", "danger");
    }
  });

  // Education & Skills Form Submit
  document.getElementById("profile-edu-skills-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const gradVal = document.getElementById("prof-grad-year").value;
    const payload = {
      highest_qualification: document.getElementById("prof-highest-qual").value.trim(),
      degree: document.getElementById("prof-degree").value.trim(),
      college_university: document.getElementById("prof-college").value.trim(),
      graduation_year: gradVal ? parseInt(gradVal) : null,
      cgpa_or_percentage: document.getElementById("prof-cgpa").value.trim(),
      programming_languages: document.getElementById("prof-prog-langs").value.trim(),
      frameworks: document.getElementById("prof-frameworks").value.trim(),
      testing_tools: document.getElementById("prof-testing-tools").value.trim(),
      databases: document.getElementById("prof-databases").value.trim()
    };

    try {
      await api.put("/profile", payload);
      showToast("Education and technical skills saved!");
      loadProfileData();
    } catch (err) {
      showToast(err.message || "Failed to save education & skills.", "danger");
    }
  });

  // Links Form Submit
  document.getElementById("profile-links-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const linkedin_url = document.getElementById("prof-linkedin").value.trim();
    const github_url = document.getElementById("prof-github").value.trim();
    const portfolio_url = document.getElementById("prof-portfolio").value.trim();
    const projects_json = document.getElementById("prof-projects").value.trim();

    if (linkedin_url) {
      const err = validateUrl(linkedin_url, "LinkedIn");
      if (err) { showToast(err, "danger"); return; }
    }
    if (github_url) {
      const err = validateUrl(github_url, "GitHub");
      if (err) { showToast(err, "danger"); return; }
    }

    try {
      await api.put("/profile", { linkedin_url, github_url, portfolio_url, projects_json });
      showToast("Online profile links and projects saved!");
      loadProfileData();
    } catch (err) {
      showToast(err.message || "Failed to save links.", "danger");
    }
  });

  // Settings & Security Form Submit with strict validation
  document.getElementById("profile-settings-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const full_name = document.getElementById("settings-name").value.trim();
    const email = document.getElementById("settings-email").value.trim();
    const phone = document.getElementById("settings-phone").value.trim();
    const old_password = document.getElementById("settings-old-pass").value;
    const new_password = document.getElementById("settings-new-pass").value;

    const nameErr = validateFullName(full_name);
    if (nameErr) { showToast(nameErr, "danger"); return; }

    const emailErr = validateEmail(email);
    if (emailErr) { showToast(emailErr, "danger"); return; }

    if (phone) {
      const phoneErr = validatePhone(phone);
      if (phoneErr) { showToast(phoneErr, "danger"); return; }
    }

    const payload = { full_name, email, phone };
    if (new_password) {
      if (!old_password) {
        showToast("Please enter your current password to set a new password.", "danger");
        return;
      }
      if (new_password.length < 6) {
        showToast("New password must be at least 6 characters.", "danger");
        return;
      }
      payload.old_password = old_password;
      payload.new_password = new_password;
    }

    try {
      await api.put("/profile/settings", payload);
      showToast("Account credentials updated successfully!");
      document.getElementById("settings-old-pass").value = "";
      document.getElementById("settings-new-pass").value = "";
      loadProfileData();
    } catch (err) {
      showToast(err.message || "Failed to update account settings.", "danger");
    }
  });

  loadProfileData();
}

async function loadProfileData() {
  try {
    const profile = await api.get("/profile");
    if (!profile) return;

    // Header & Avatar
    document.getElementById("profile-header-name").textContent = profile.full_name || "User";
    document.getElementById("profile-header-headline").textContent = profile.headline || "Complete your profile to unlock job recommendations";

    const contactParts = [];
    if (profile.email) contactParts.push(`${getIcon("mail", "", 13)} ${profile.email}`);
    if (profile.phone) contactParts.push(`${getIcon("phone", "", 13)} ${profile.phone}`);
    if (profile.city) contactParts.push(`${getIcon("map-pin", "", 13)} ${profile.city}, ${profile.state || 'India'}`);
    document.getElementById("profile-header-contact").innerHTML = contactParts.join("<span style='color: var(--border-color);'>&bull;</span>");

    const avatarImg = document.getElementById("profile-avatar-img");
    const avatarInitials = document.getElementById("profile-avatar-initials");
    const removeBtn = document.getElementById("btn-remove-avatar");

    if (profile.avatar_url) {
      avatarImg.src = getAuthenticatedFileUrl(profile.avatar_url);
      avatarImg.style.display = "block";
      avatarInitials.style.display = "none";
      if (removeBtn) removeBtn.style.display = "inline-flex";
    } else {
      avatarImg.style.display = "none";
      const initials = (profile.full_name || "US").split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
      avatarInitials.textContent = initials;
      avatarInitials.style.display = "inline-block";
      if (removeBtn) removeBtn.style.display = "none";
    }

    // Completeness
    const score = profile.completeness_score || 0;
    document.getElementById("profile-completeness-text").textContent = `${score}%`;
    document.getElementById("profile-completeness-bar").style.width = `${score}%`;

    // Fill Personal Form
    const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ""; };
    setVal("prof-city", profile.city);
    setVal("prof-state", profile.state);
    setVal("prof-country", profile.country || "India");

    // Fill Professional Form
    setVal("prof-headline", profile.headline);
    setVal("prof-objective", profile.career_objective);
    setVal("prof-pref-roles", profile.preferred_roles);
    setVal("prof-pref-locations", profile.preferred_locations);
    setVal("prof-pref-emp", profile.employment_preference || "FULL_TIME");
    setVal("prof-expected-salary", profile.expected_salary);
    setVal("prof-notice-period", profile.notice_period_days);

    // Fill Education & Skills Form
    setVal("prof-highest-qual", profile.highest_qualification);
    setVal("prof-degree", profile.degree);
    setVal("prof-college", profile.college_university);
    setVal("prof-grad-year", profile.graduation_year);
    setVal("prof-cgpa", profile.cgpa_or_percentage);
    setVal("prof-prog-langs", profile.programming_languages);
    setVal("prof-frameworks", profile.frameworks);
    setVal("prof-testing-tools", profile.testing_tools);
    setVal("prof-databases", profile.databases);

    // Fill Links Form
    setVal("prof-linkedin", profile.linkedin_url);
    setVal("prof-github", profile.github_url);
    setVal("prof-portfolio", profile.portfolio_url);
    setVal("prof-projects", profile.projects_json);

    // Fill Settings Form & Verification Status
    setVal("settings-name", profile.full_name);
    setVal("settings-email", profile.email);
    setVal("settings-phone", profile.phone);

    // Email verification state
    const emailBadge = document.getElementById("badge-email-status");
    const emailLabel = document.getElementById("label-email-val");
    const emailBtn = document.getElementById("btn-verify-email-action");
    if (emailBadge && emailLabel && emailBtn) {
      emailLabel.textContent = profile.email || "No email";
      if (profile.is_email_verified) {
        emailBadge.className = "badge-status badge-success";
        emailBadge.innerHTML = `${getIcon("check", "", 12)} Verified`;
        emailBtn.style.display = "none";
      } else {
        emailBadge.className = "badge-status badge-warning";
        emailBadge.innerHTML = `${getIcon("alert-circle", "", 12)} Unverified`;
        emailBtn.style.display = "inline-flex";
        emailBtn.onclick = async () => {
          try {
            showToast("Sending email verification link...", "info");
            const res = await api.post("/auth/verify-email/request");
            showToast(res.message || "Verification email sent!");
            if (res.is_verified) loadProfileData();
          } catch (err) {
            showToast(err.message || "Failed to send verification email.", "danger");
          }
        };
      }
    }

    // Phone verification state
    const phoneBadge = document.getElementById("badge-phone-status");
    const phoneLabel = document.getElementById("label-phone-val");
    const phoneBtn = document.getElementById("btn-verify-phone-action");
    if (phoneBadge && phoneLabel && phoneBtn) {
      phoneLabel.textContent = profile.phone || "No phone entered";
      if (profile.is_phone_verified) {
        phoneBadge.className = "badge-status badge-success";
        phoneBadge.innerHTML = `${getIcon("check", "", 12)} Verified`;
        phoneBtn.style.display = "none";
      } else {
        phoneBadge.className = "badge-status badge-warning";
        phoneBadge.innerHTML = `${getIcon("alert-circle", "", 12)} Unverified`;
        phoneBtn.style.display = profile.phone ? "inline-flex" : "none";
        phoneBtn.onclick = () => openPhoneOtpModal(profile.phone);
      }
    }

  } catch (err) {
    console.warn("Failed to load profile data:", err);
  }
}

function openPhoneOtpModal(phone) {
  const content = `
    <div style="display: flex; flex-direction: column; gap: 1rem;">
      <p style="font-size: 0.875rem; color: var(--text-secondary); margin: 0;">
        We sent a 6-digit verification code to <strong>${phone}</strong>. Enter the OTP code below to verify your mobile number.
      </p>
      <div class="form-group">
        <label>Enter 6-Digit OTP</label>
        <input type="text" id="otp-input" maxlength="6" class="form-control" style="font-size: 1.25rem; letter-spacing: 0.35em; text-align: center;" placeholder="123456" />
      </div>
      <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem;">
        <button type="button" id="btn-resend-otp" class="btn btn-ghost btn-sm" style="font-size: 0.8rem;">Resend Code</button>
        <div style="display: flex; gap: 0.5rem;">
          <button type="button" class="btn btn-outline close-modal-btn">Cancel</button>
          <button type="button" id="btn-submit-otp" class="btn btn-primary">Verify OTP</button>
        </div>
      </div>
    </div>
  `;

  const { closeModal } = createModal("Mobile OTP Verification", content);

  // Send initial OTP
  api.post("/auth/verify-phone/request-otp", { phone }).then(res => {
    showToast(res.message || "OTP sent!");
  }).catch(err => {
    showToast(err.message || "Failed to trigger OTP.", "danger");
  });

  document.getElementById("btn-resend-otp")?.addEventListener("click", async () => {
    try {
      showToast("Resending OTP...", "info");
      const res = await api.post("/auth/verify-phone/request-otp", { phone });
      showToast(res.message || "New OTP sent!");
    } catch (err) {
      showToast(err.message || "Failed to resend OTP.", "danger");
    }
  });

  document.getElementById("btn-submit-otp")?.addEventListener("click", async () => {
    const otp = document.getElementById("otp-input").value.trim();
    if (!otp || otp.length !== 6) {
      showToast("Please enter a valid 6-digit OTP.", "danger");
      return;
    }

    try {
      const res = await api.post("/auth/verify-phone/confirm-otp", { phone, otp });
      showToast(res.message || "Phone verified successfully!");
      closeModal();
      loadProfileData();
    } catch (err) {
      showToast(err.message || "Invalid OTP code.", "danger");
    }
  });
}
