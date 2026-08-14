import { api } from "../api.js";
import { showToast } from "../components.js";

export function renderProfile() {
  return `
    <div class="view-header">
      <div>
        <h1 class="view-title">👤 Student Talent Profile & Settings</h1>
        <p class="view-subtitle">Manage your personal information, career objective, education, skills, preferences, and account security.</p>
      </div>
    </div>

    <!-- Top Card: Profile Completeness Score & Hero Avatar -->
    <div class="card" style="margin-bottom: 1.5rem; background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%);">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1.25rem;">
        <div style="display: flex; align-items: center; gap: 1.25rem;">
          <div style="position: relative;">
            <img id="profile-avatar-img" src="./favicon.svg" alt="Avatar" style="width: 76px; height: 76px; border-radius: 50%; object-fit: cover; border: 3px solid var(--primary-color); background-color: var(--bg-tertiary);" />
            <label for="avatar-upload-input" style="position: absolute; bottom: 0; right: 0; background: var(--primary-color); color: #fff; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 0.75rem; box-shadow: var(--shadow-sm);" title="Upload Profile Picture">📷</label>
            <input type="file" id="avatar-upload-input" accept="image/*" style="display: none;" />
          </div>
          <div>
            <h3 id="profile-header-name" style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.2rem;">-</h3>
            <p id="profile-header-headline" style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.25rem;">-</p>
            <div id="profile-header-contact" style="font-size: 0.775rem; color: var(--text-muted); display: flex; gap: 0.75rem; flex-wrap: wrap;"></div>
          </div>
        </div>

        <div style="min-width: 260px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
            <span style="font-size: 0.8rem; font-weight: 700; color: var(--text-primary);">Profile Completeness</span>
            <span id="profile-completeness-text" style="font-size: 0.85rem; font-weight: 700; color: var(--primary-color);">0%</span>
          </div>
          <div style="width: 100%; height: 10px; background-color: var(--border-color); border-radius: 999px; overflow: hidden;">
            <div id="profile-completeness-bar" style="width: 0%; height: 100%; background: linear-gradient(90deg, var(--primary-color), var(--accent-color)); transition: width var(--transition-medium);"></div>
          </div>
          <div id="profile-missing-items" style="font-size: 0.7rem; color: var(--warning-color); margin-top: 0.4rem;"></div>
        </div>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="tabs-header" style="display: flex; gap: 0.5rem; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; flex-wrap: wrap;">
      <button class="btn btn-outline profile-tab-btn active" data-tab="tab-personal">Personal & Contact</button>
      <button class="btn btn-outline profile-tab-btn" data-tab="tab-professional">Professional & Objective</button>
      <button class="btn btn-outline profile-tab-btn" data-tab="tab-education">Education & Skills</button>
      <button class="btn btn-outline profile-tab-btn" data-tab="tab-links">Projects & Links</button>
      <button class="btn btn-outline profile-tab-btn" data-tab="tab-settings">Account & Security</button>
    </div>

    <!-- Tab 1: Personal Information -->
    <div id="tab-personal" class="profile-tab-content card">
      <h3 style="font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem;">Personal Information</h3>
      <form id="profile-personal-form" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">
        <div class="form-group">
          <label>City</label>
          <input type="text" id="prof-city" class="form-control" placeholder="e.g. Pune" />
        </div>
        <div class="form-group">
          <label>State</label>
          <input type="text" id="prof-state" class="form-control" placeholder="e.g. Maharashtra" />
        </div>
        <div class="form-group">
          <label>Country</label>
          <input type="text" id="prof-country" class="form-control" value="India" />
        </div>
        <div style="grid-column: 1 / -1; display: flex; justify-content: flex-end;">
          <button type="submit" id="btn-save-personal" class="btn btn-primary">Save Personal Info</button>
        </div>
      </form>
    </div>

    <!-- Tab 2: Professional Information -->
    <div id="tab-professional" class="profile-tab-content card" style="display: none;">
      <h3 style="font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem;">Professional & Career Preferences</h3>
      <form id="profile-professional-form" style="display: flex; flex-direction: column; gap: 1rem;">
        <div class="form-group">
          <label>Headline / Tagline</label>
          <input type="text" id="prof-headline" class="form-control" placeholder="e.g. QA Automation Specialist | Selenium & Java" />
        </div>
        <div class="form-group">
          <label>Career Objective</label>
          <textarea id="prof-objective" class="form-control" rows="3" placeholder="Describe your career goals and ideal role..."></textarea>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">
          <div class="form-group">
            <label>Preferred Roles (Comma separated)</label>
            <input type="text" id="prof-pref-roles" class="form-control" placeholder="QA Engineer, Automation Engineer" />
          </div>
          <div class="form-group">
            <label>Preferred Locations (Comma separated)</label>
            <input type="text" id="prof-pref-locations" class="form-control" placeholder="Pune, Bengaluru, Remote" />
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
            <label>Expected Salary (INR / Annum)</label>
            <input type="number" id="prof-expected-salary" class="form-control" placeholder="600000" />
          </div>
          <div class="form-group">
            <label>Notice Period / Availability (Days)</label>
            <input type="number" id="prof-notice-period" class="form-control" placeholder="15" />
          </div>
        </div>
        <div style="display: flex; justify-content: flex-end;">
          <button type="submit" id="btn-save-professional" class="btn btn-primary">Save Professional Preferences</button>
        </div>
      </form>
    </div>

    <!-- Tab 3: Education & Skills -->
    <div id="tab-education" class="profile-tab-content card" style="display: none;">
      <h3 style="font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem;">Education & Technical Skills</h3>
      <form id="profile-edu-skills-form" style="display: flex; flex-direction: column; gap: 1rem;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">
          <div class="form-group">
            <label>Highest Qualification</label>
            <input type="text" id="prof-highest-qual" class="form-control" placeholder="Bachelor of Engineering" />
          </div>
          <div class="form-group">
            <label>Degree Name</label>
            <input type="text" id="prof-degree" class="form-control" placeholder="B.E. Computer Science" />
          </div>
          <div class="form-group">
            <label>College / University</label>
            <input type="text" id="prof-college" class="form-control" placeholder="Savitribai Phule Pune University" />
          </div>
          <div class="form-group">
            <label>Graduation Year</label>
            <input type="number" id="prof-grad-year" class="form-control" placeholder="2025" />
          </div>
          <div class="form-group">
            <label>CGPA / Percentage</label>
            <input type="text" id="prof-cgpa" class="form-control" placeholder="8.4 CGPA or 78%" />
          </div>
        </div>

        <h4 style="font-size: 0.95rem; font-weight: 700; margin-top: 0.5rem; color: var(--text-primary);">Skills Inventory</h4>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">
          <div class="form-group">
            <label>Programming Languages</label>
            <input type="text" id="prof-prog-langs" class="form-control" placeholder="Java, Python, JavaScript" />
          </div>
          <div class="form-group">
            <label>Testing & Automation Tools</label>
            <input type="text" id="prof-testing-tools" class="form-control" placeholder="Selenium, TestNG, Playwright, Postman" />
          </div>
          <div class="form-group">
            <label>Frameworks & Libraries</label>
            <input type="text" id="prof-frameworks" class="form-control" placeholder="Spring Boot, React, FastAPI" />
          </div>
          <div class="form-group">
            <label>Databases & Cloud</label>
            <input type="text" id="prof-databases" class="form-control" placeholder="MySQL, PostgreSQL, AWS, Docker" />
          </div>
        </div>

        <div style="display: flex; justify-content: flex-end;">
          <button type="submit" id="btn-save-education" class="btn btn-primary">Save Education & Skills</button>
        </div>
      </form>
    </div>

    <!-- Tab 4: Projects & Links -->
    <div id="tab-links" class="profile-tab-content card" style="display: none;">
      <h3 style="font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem;">Projects & Social Profiles</h3>
      <form id="profile-links-form" style="display: flex; flex-direction: column; gap: 1rem;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">
          <div class="form-group">
            <label>LinkedIn Profile URL</label>
            <input type="url" id="prof-linkedin" class="form-control" placeholder="https://linkedin.com/in/yourprofile" />
          </div>
          <div class="form-group">
            <label>GitHub Profile URL</label>
            <input type="url" id="prof-github" class="form-control" placeholder="https://github.com/yourusername" />
          </div>
          <div class="form-group">
            <label>Portfolio / Website URL</label>
            <input type="url" id="prof-portfolio" class="form-control" placeholder="https://yourportfolio.com" />
          </div>
        </div>
        <div class="form-group">
          <label>Key Projects (Summary / Tech used)</label>
          <textarea id="prof-projects" class="form-control" rows="3" placeholder="Project 1: E-commerce Test Automation Suite (Selenium + TestNG) ..."></textarea>
        </div>
        <div style="display: flex; justify-content: flex-end;">
          <button type="submit" id="btn-save-links" class="btn btn-primary">Save Projects & Links</button>
        </div>
      </form>
    </div>

    <!-- Tab 5: Account & Security -->
    <div id="tab-settings" class="profile-tab-content card" style="display: none;">
      <h3 style="font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem;">Account Settings & Security</h3>
      <form id="profile-settings-form" style="display: flex; flex-direction: column; gap: 1rem; max-width: 480px;">
        <div class="form-group">
          <label>Full Name *</label>
          <input type="text" id="settings-name" required class="form-control" />
        </div>
        <div class="form-group">
          <label>Email Address *</label>
          <input type="email" id="settings-email" required class="form-control" />
        </div>
        <div class="form-group">
          <label>Phone Number</label>
          <input type="text" id="settings-phone" class="form-control" />
        </div>
        
        <h4 style="font-size: 0.95rem; font-weight: 700; margin-top: 1rem; border-top: 1px solid var(--border-color); padding-top: 1rem;">Change Password</h4>
        <div class="form-group">
          <label>Current Password</label>
          <input type="password" id="settings-old-pass" class="form-control" placeholder="Leave empty to keep current password" />
        </div>
        <div class="form-group">
          <label>New Password</label>
          <input type="password" id="settings-new-pass" class="form-control" placeholder="Minimum 6 characters" />
        </div>
        
        <div style="display: flex; justify-content: flex-end;">
          <button type="submit" id="btn-save-settings" class="btn btn-primary">Update Account Settings</button>
        </div>
      </form>
    </div>
  `;
}

export function initProfileListeners() {
  // Tab switching logic
  const tabBtns = document.querySelectorAll(".profile-tab-btn");
  const tabContents = document.querySelectorAll(".profile-tab-content");

  const activateTab = (tabId) => {
    tabBtns.forEach(b => {
      const match = b.getAttribute("data-tab") === tabId;
      b.classList.toggle("active", match);
    });
    tabContents.forEach(c => {
      c.style.display = c.id === tabId ? "block" : "none";
    });
  };

  tabBtns.forEach(btn => {
    btn.onclick = () => {
      const targetId = btn.getAttribute("data-tab");
      activateTab(targetId);
    };
  });

  // Check URL query string for active tab e.g. #/profile?tab=tab-settings
  if (window.location.hash.includes("tab=")) {
    const queryTab = window.location.hash.split("tab=")[1];
    if (queryTab) {
      const fullTabId = queryTab.startsWith("tab-") ? queryTab : `tab-${queryTab}`;
      activateTab(fullTabId);
    }
  }

  // Avatar upload with loading state
  const avatarInput = document.getElementById("avatar-upload-input");
  if (avatarInput) {
    avatarInput.onchange = async (e) => {
      if (e.target.files && e.target.files.length > 0) {
        const formData = new FormData();
        formData.append("file", e.target.files[0]);
        try {
          showToast("Uploading profile picture...", "info");
          const res = await api.post("/profile/avatar", formData, false);
          document.getElementById("profile-avatar-img").src = res.avatar_url;
          showToast("Profile picture updated successfully!");
        } catch (err) {
          showToast(err.message || "Failed to upload avatar.", "danger");
        }
      }
    };
  }

  // Load Profile Data
  loadProfileData();

  // Form submits with loading state button indicators
  bindFormSubmit("profile-personal-form", "btn-save-personal", getPersonalPayload);
  bindFormSubmit("profile-professional-form", "btn-save-professional", getProfessionalPayload);
  bindFormSubmit("profile-edu-skills-form", "btn-save-education", getEduSkillsPayload);
  bindFormSubmit("profile-links-form", "btn-save-links", getLinksPayload);

  // Settings form submit
  const settingsForm = document.getElementById("profile-settings-form");
  const settingsBtn = document.getElementById("btn-save-settings");
  if (settingsForm && settingsBtn) {
    settingsForm.onsubmit = async (e) => {
      e.preventDefault();
      const origText = settingsBtn.textContent;
      settingsBtn.disabled = true;
      settingsBtn.textContent = "Updating...";

      const full_name = document.getElementById("settings-name").value.trim();
      const email = document.getElementById("settings-email").value.trim();
      const phone = document.getElementById("settings-phone").value.trim();
      const old_password = document.getElementById("settings-old-pass").value;
      const new_password = document.getElementById("settings-new-pass").value;

      try {
        await api.put("/profile/settings", { full_name, email, phone, old_password, new_password });
        showToast("Account settings updated successfully!");
        document.getElementById("settings-old-pass").value = "";
        document.getElementById("settings-new-pass").value = "";
        loadProfileData();
      } catch (err) {
        showToast(err.message || "Failed to update account settings.", "danger");
      } finally {
        settingsBtn.disabled = false;
        settingsBtn.textContent = origText;
      }
    };
  }
}

async function loadProfileData() {
  try {
    const p = await api.get("/profile");

    // Top Header & Widget
    const nameEl = document.getElementById("profile-header-name");
    const headlineEl = document.getElementById("profile-header-headline");
    const contactEl = document.getElementById("profile-header-contact");

    if (nameEl) nameEl.textContent = p.full_name;
    if (headlineEl) headlineEl.textContent = p.headline || "Add your career headline...";
    if (contactEl) {
      contactEl.innerHTML = `
        <span>📧 ${p.email}</span>
        ${p.phone ? `<span>📞 ${p.phone}</span>` : ''}
        ${p.city ? `<span>📍 ${p.city}, ${p.country || 'India'}</span>` : ''}
      `;
    }

    if (p.avatar_url) {
      const avatarImg = document.getElementById("profile-avatar-img");
      if (avatarImg) avatarImg.src = p.avatar_url;
    }

    const pct = p.completeness_score || 0;
    const scoreText = document.getElementById("profile-completeness-text");
    const scoreBar = document.getElementById("profile-completeness-bar");
    if (scoreText) scoreText.textContent = `${pct}%`;
    if (scoreBar) scoreBar.style.width = `${pct}%`;

    const missingEl = document.getElementById("profile-missing-items");
    if (missingEl) {
      if (p.missing_items && p.missing_items.length > 0) {
        missingEl.textContent = `Missing: ${p.missing_items.join(" • ")}`;
      } else {
        missingEl.textContent = "✓ Profile complete!";
        missingEl.style.color = "var(--accent-color)";
      }
    }

    // Populate Tab 1: Personal
    setVal("prof-city", p.city);
    setVal("prof-state", p.state);
    setVal("prof-country", p.country || "India");

    // Populate Tab 2: Professional
    setVal("prof-headline", p.headline);
    setVal("prof-objective", p.career_objective);
    setVal("prof-pref-roles", p.preferred_roles);
    setVal("prof-pref-locations", p.preferred_locations);
    setVal("prof-pref-emp", p.employment_preference || "FULL_TIME");
    setVal("prof-expected-salary", p.expected_salary);
    setVal("prof-notice-period", p.notice_period_days);

    // Populate Tab 3: Education & Skills
    setVal("prof-highest-qual", p.highest_qualification);
    setVal("prof-degree", p.degree);
    setVal("prof-college", p.college_university);
    setVal("prof-grad-year", p.graduation_year);
    setVal("prof-cgpa", p.cgpa_or_percentage);
    setVal("prof-prog-langs", p.programming_languages);
    setVal("prof-testing-tools", p.testing_tools);
    setVal("prof-frameworks", p.frameworks);
    setVal("prof-databases", p.databases);

    // Populate Tab 4: Links & Projects
    setVal("prof-linkedin", p.linkedin_url);
    setVal("prof-github", p.github_url);
    setVal("prof-portfolio", p.portfolio_url);
    setVal("prof-projects", p.projects_json);

    // Populate Tab 5: Settings
    setVal("settings-name", p.full_name);
    setVal("settings-email", p.email);
    setVal("settings-phone", p.phone);

  } catch (err) {
    showToast(err.message || "Failed to load profile.", "danger");
  }
}

function setVal(id, val) {
  const el = document.getElementById(id);
  if (el) el.value = val || "";
}

function getVal(id) {
  const el = document.getElementById(id);
  return el ? el.value.trim() : null;
}

function bindFormSubmit(formId, btnId, payloadGetter) {
  const form = document.getElementById(formId);
  const btn = document.getElementById(btnId);
  if (form && btn) {
    form.onsubmit = async (e) => {
      e.preventDefault();
      const origText = btn.textContent;
      btn.disabled = true;
      btn.textContent = "Saving...";
      const payload = payloadGetter();
      try {
        await api.put("/profile", payload);
        showToast("Profile section saved successfully!");
        loadProfileData();
      } catch (err) {
        showToast(err.message || "Failed to save profile.", "danger");
      } finally {
        btn.disabled = false;
        btn.textContent = origText;
      }
    };
  }
}

function getPersonalPayload() {
  return {
    city: getVal("prof-city"),
    state: getVal("prof-state"),
    country: getVal("prof-country")
  };
}

function getProfessionalPayload() {
  return {
    headline: getVal("prof-headline"),
    career_objective: getVal("prof-objective"),
    preferred_roles: getVal("prof-pref-roles"),
    preferred_locations: getVal("prof-pref-locations"),
    employment_preference: getVal("prof-pref-emp"),
    expected_salary: getVal("prof-expected-salary") ? parseFloat(getVal("prof-expected-salary")) : null,
    notice_period_days: getVal("prof-notice-period") ? parseInt(getVal("prof-notice-period")) : null
  };
}

function getEduSkillsPayload() {
  return {
    highest_qualification: getVal("prof-highest-qual"),
    degree: getVal("prof-degree"),
    college_university: getVal("prof-college"),
    graduation_year: getVal("prof-grad-year") ? parseInt(getVal("prof-grad-year")) : null,
    cgpa_or_percentage: getVal("prof-cgpa"),
    programming_languages: getVal("prof-prog-langs"),
    testing_tools: getVal("prof-testing-tools"),
    frameworks: getVal("prof-frameworks"),
    databases: getVal("prof-databases")
  };
}

function getLinksPayload() {
  return {
    linkedin_url: getVal("prof-linkedin"),
    github_url: getVal("prof-github"),
    portfolio_url: getVal("prof-portfolio"),
    projects_json: getVal("prof-projects")
  };
}
