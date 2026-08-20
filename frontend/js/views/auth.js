import { api, API } from "../api.js";
import { store } from "../store.js";
import {
  showToast,
  initPasswordToggle,
  initPasswordStrengthIndicator,
  validateFullName,
  validateEmail
} from "../components.js";
import { getIcon } from "../icons.js";
import { ROLE_CONFIG, ROLES } from "../permissions.js";

/**
 * 3 Core Account Types for NxtMov
 */
/**
 * 3 Core Account Types for NxtMov Login Screen
 */
const SELECTABLE_ACCOUNT_ROLES = [
  {
    roleKey: "STUDENT",
    urlParam: "student",
    title: "Student",
    badgeLabel: "Talent / Candidate",
    badgeClass: "badge-student",
    icon: "graduation-cap",
    accentColor: "#10b981",
    accentBg: "rgba(16, 185, 129, 0.12)",
    placeholder: "student@example.com",
    label: "Student Email / Username",
    description: "Manage your profile, ATS resume scores, matched opportunities, and application progress."
  },
  {
    roleKey: "MENTOR",
    urlParam: "mentor",
    title: "Mentor",
    badgeLabel: "Career Guide",
    badgeClass: "badge-mentor",
    icon: "user-check",
    accentColor: "#a855f7",
    accentBg: "rgba(168, 85, 247, 0.12)",
    placeholder: "faculty@institute.edu",
    label: "Official Mentor Email",
    description: "Guide students, review progress, inspect ATS readiness, and conduct mentoring sessions."
  },
  {
    roleKey: "ADMIN",
    urlParam: "admin",
    title: "Administrator",
    badgeLabel: "Platform Admin",
    badgeClass: "badge-admin",
    icon: "shield-check",
    accentColor: "#ef4444",
    accentBg: "rgba(239, 68, 68, 0.12)",
    placeholder: "admin@nxtmov.local",
    label: "Administrator Email",
    description: "Oversee platform users, mentor approvals, organizations, and governance settings."
  }
];

/**
 * Extracts and canonicalizes requested role from window.location.hash
 */
function getSelectedRoleFromHash() {
  const hash = window.location.hash || "";
  if (!hash.includes("?")) return null;

  const queryString = hash.split("?")[1] || "";
  const params = new URLSearchParams(queryString);
  const rawRole = (params.get("role") || "").toLowerCase().trim();

  if (!rawRole) return null;

  const found = SELECTABLE_ACCOUNT_ROLES.find(
    r => r.urlParam === rawRole || r.roleKey.toLowerCase() === rawRole
  );

  return found ? found.roleKey : null;
}

/**
 * Master render function for /login — Unified Single-Screen Login with 3-Role Selector
 */
export function renderLogin() {
  const selectedRoleKey = getSelectedRoleFromHash() || "STUDENT";
  const activeRole = SELECTABLE_ACCOUNT_ROLES.find(r => r.roleKey === selectedRoleKey) || SELECTABLE_ACCOUNT_ROLES[0];

  return `
    <div class="auth-card card" style="max-width: 480px; margin: 2.25rem auto; padding: 2.25rem 2rem; border-radius: var(--radius-xl); box-shadow: var(--shadow-lg);">
      <!-- Header -->
      <div style="text-align: center; margin-bottom: 1.5rem;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 48px; height: 48px; border-radius: 14px; background: linear-gradient(135deg, rgba(79, 70, 229, 0.15) 0%, rgba(99, 102, 241, 0.05) 100%); color: var(--primary-color); margin-bottom: 0.85rem; box-shadow: 0 2px 8px rgba(79, 70, 229, 0.12);">
          ${getIcon("users", "", 24)}
        </div>
        <h2 style="margin: 0 0 0.35rem 0; color: var(--text-primary); font-size: 1.5rem; font-weight: 800; letter-spacing: -0.02em;">
          Sign In to NxtMov
        </h2>
        <p style="color: var(--text-muted); margin: 0; font-size: 0.85rem; line-height: 1.4;">
          Select your role and enter your credentials to access your tailored workspace.
        </p>
      </div>

      <!-- 3-Option Role Selector -->
      <div style="margin-bottom: 1.25rem;">
        <label style="display: block; margin-bottom: 0.45rem; font-size: 0.775rem; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px;">
          Select Account Role *
        </label>
        <div class="role-segmented-selector" role="tablist" aria-label="Select your role">
          ${SELECTABLE_ACCOUNT_ROLES.map(role => {
            const isActive = role.roleKey === activeRole.roleKey;
            const activeClass = isActive ? `active role-${role.urlParam}` : "";
            return `
              <button
                type="button"
                class="role-selector-tab ${activeClass}"
                role="tab"
                aria-selected="${isActive ? 'true' : 'false'}"
                id="role-tab-${role.urlParam}"
                data-role-key="${role.roleKey}"
                data-role-param="${role.urlParam}"
                data-title="${role.title}"
                data-placeholder="${role.placeholder}"
                data-label="${role.label}"
                data-description="${role.description}"
                data-accent-color="${role.accentColor}"
                data-accent-bg="${role.accentBg}"
                tabindex="0"
              >
                <div class="role-tab-icon" style="background: ${role.accentBg}; color: ${role.accentColor};">
                  ${getIcon(role.icon, "", 16)}
                </div>
                <div class="role-tab-title">${role.title}</div>
                <span class="role-tab-badge ${role.badgeClass}">${role.title}</span>
              </button>
            `;
          }).join("")}
        </div>
        <p id="role-selected-caption" style="font-size: 0.775rem; color: var(--text-secondary); margin: -0.75rem 0 1rem 0; line-height: 1.4; padding: 0.5rem 0.75rem; background: var(--bg-secondary); border-radius: var(--radius-md); border-left: 3px solid ${activeRole.accentColor};">
          ${activeRole.description}
        </p>
      </div>

      <!-- Error / Status Container -->
      <div id="login-error-container" style="display: none; margin-bottom: 1.25rem; padding: 0.75rem 1rem; border-radius: var(--radius-md); background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger-color); color: var(--danger-color); font-size: 0.85rem; line-height: 1.4; align-items: center; gap: 0.5rem;">
        <span style="flex-shrink: 0;">${getIcon("alert-circle", "", 16)}</span>
        <span id="login-error-text"></span>
      </div>

      <!-- Quick Test Accounts Helper -->
      <div id="demo-credentials-container" style="margin-bottom: 1.25rem; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 0.75rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
          <span style="font-size: 0.725rem; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 0.35rem;">
            ${getIcon("sparkles", "", 13)} Quick Test Credentials
          </span>
          <span class="badge-status badge-info" style="font-size: 0.6rem;">EVALUATION</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.35rem;">
          <button type="button" class="btn btn-outline quick-fill-btn" data-fill-role="STUDENT" data-email="student.tester@example.com" data-pass="Password123!" style="font-size: 0.7rem; padding: 0.25rem 0.35rem; justify-content: center;">
            Student Fill
          </button>
          <button type="button" class="btn btn-outline quick-fill-btn" data-fill-role="MENTOR" data-email="prof.mentor@example.edu" data-pass="MentorPass123!" style="font-size: 0.7rem; padding: 0.25rem 0.35rem; justify-content: center;">
            Mentor Fill
          </button>
          <button type="button" class="btn btn-outline quick-fill-btn" data-fill-role="ADMIN" data-email="demo@nxtmov.local" data-pass="NxtMov@123" style="font-size: 0.7rem; padding: 0.25rem 0.35rem; justify-content: center;">
            Admin Fill
          </button>
        </div>
      </div>

      <!-- Login Form -->
      <form id="login-form" novalidate data-selected-role="${activeRole.roleKey}">
        <div class="form-group" style="margin-bottom: 1rem;">
          <label id="login-email-label" style="display: block; margin-bottom: 0.45rem; font-size: 0.85rem; font-weight: 600; color: var(--text-primary);">
            ${activeRole.label} *
          </label>
          <div style="position: relative;">
            <input
              type="email"
              id="login-email"
              required
              placeholder="${activeRole.placeholder}"
              class="form-input"
              style="width: 100%; padding-left: 2.25rem;"
              autocomplete="email"
            >
            <span style="position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none;">
              ${getIcon("mail", "", 16)}
            </span>
          </div>
        </div>

        <div class="form-group" style="margin-bottom: 1.25rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.45rem;">
            <label style="font-size: 0.85rem; font-weight: 600; margin: 0; color: var(--text-primary);">Password *</label>
            <a href="#/forgot-password" style="font-size: 0.775rem; color: var(--primary-color); font-weight: 500;">Forgot password?</a>
          </div>
          <div style="position: relative;">
            <input
              type="password"
              id="login-password"
              required
              placeholder="••••••••"
              class="form-input"
              style="width: 100%; padding-left: 2.25rem;"
              autocomplete="current-password"
            >
            <span style="position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none;">
              ${getIcon("lock", "", 16)}
            </span>
          </div>
        </div>

        <button
          type="submit"
          id="login-submit-btn"
          class="btn btn-primary"
          style="width: 100%; justify-content: center; gap: 0.5rem; padding: 0.7rem 1rem; font-weight: 600; font-size: 0.9rem; border-radius: var(--radius-md);"
        >
          Sign In as ${activeRole.title}
        </button>
      </form>

      <!-- Bottom Switch Links -->
      <div style="text-align: center; margin-top: 1.5rem; font-size: 0.825rem; color: var(--text-secondary); border-top: 1px solid var(--border-color); padding-top: 1.25rem; display: flex; flex-direction: column; gap: 0.4rem;">
        <div>
          New student? <a href="#/register" style="color: var(--primary-color); font-weight: 600;">Student Sign Up</a>
        </div>
        <div>
          Want to guide talent? <a href="#/apply-mentor" style="color: #a855f7; font-weight: 600;">Apply as Mentor</a> • <a href="#/admin-bootstrap" style="color: #ef4444; font-weight: 600;">Bootstrap Admin</a>
        </div>
      </div>
    </div>
  `;
}

/**
 * Attaches interactive event listeners to /login
 */
export function initLoginListeners() {
  const form = document.getElementById("login-form");
  if (!form) return;

  const emailInput = document.getElementById("login-email");
  const passwordInput = document.getElementById("login-password");
  const submitBtn = document.getElementById("login-submit-btn");
  const errorContainer = document.getElementById("login-error-container");
  const errorText = document.getElementById("login-error-text");
  const emailLabel = document.getElementById("login-email-label");
  const caption = document.getElementById("role-selected-caption");
  const roleTabs = document.querySelectorAll(".role-selector-tab");

  initPasswordToggle(form);

  // Helper function to switch active role state in the UI
  const setRole = (roleKey) => {
    const roleMeta = SELECTABLE_ACCOUNT_ROLES.find(r => r.roleKey === roleKey) || SELECTABLE_ACCOUNT_ROLES[0];
    form.setAttribute("data-selected-role", roleMeta.roleKey);

    roleTabs.forEach(tab => {
      const isThis = tab.getAttribute("data-role-key") === roleMeta.roleKey;
      tab.setAttribute("aria-selected", isThis ? "true" : "false");
      tab.className = `role-selector-tab ${isThis ? `active role-${tab.getAttribute('data-role-param')}` : ''}`;
    });

    if (emailLabel) emailLabel.textContent = `${roleMeta.label} *`;
    if (emailInput) emailInput.placeholder = roleMeta.placeholder;
    if (submitBtn && !submitBtn.disabled) submitBtn.textContent = `Sign In as ${roleMeta.title}`;
    if (caption) {
      caption.textContent = roleMeta.description;
      caption.style.borderLeftColor = roleMeta.accentColor;
    }
    if (errorContainer) errorContainer.style.display = "none";
  };

  // Attach tab switch handlers
  roleTabs.forEach(tab => {
    const onSelect = () => {
      const rKey = tab.getAttribute("data-role-key");
      const rParam = tab.getAttribute("data-role-param");
      setRole(rKey);
      if (history.replaceState) {
        history.replaceState(null, "", `#/login?role=${rParam}`);
      }
    };

    tab.onclick = onSelect;
    tab.onkeydown = (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onSelect();
      }
    };
  });

  // Quick fill test buttons
  const quickFillBtns = document.querySelectorAll(".quick-fill-btn");
  quickFillBtns.forEach(btn => {
    btn.onclick = (e) => {
      e.preventDefault();
      const role = btn.getAttribute("data-fill-role");
      const email = btn.getAttribute("data-email");
      const pass = btn.getAttribute("data-pass");
      setRole(role);
      if (emailInput) emailInput.value = email;
      if (passwordInput) passwordInput.value = pass;
      showToast(`Filled ${role} credentials.`);
      submitBtn?.focus();
    };
  });

  let isSubmitting = false;

  form.onsubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    const selectedRole = form.getAttribute("data-selected-role") || "";
    const email = (emailInput?.value || "").trim();
    const password = passwordInput?.value || "";

    if (errorContainer) errorContainer.style.display = "none";

    // 1. Role presence validation
    if (!selectedRole) {
      const msg = "Please select your role.";
      if (errorContainer && errorText) {
        errorText.textContent = msg;
        errorContainer.style.display = "flex";
      }
      showToast(msg, "danger");
      return;
    }

    // 2. Credentials presence validation
    if (!email || !password) {
      const msg = "Please enter your credentials.";
      if (errorContainer && errorText) {
        errorText.textContent = msg;
        errorContainer.style.display = "flex";
      }
      showToast(msg, "danger");
      if (!email) emailInput?.focus();
      else passwordInput?.focus();
      return;
    }

    isSubmitting = true;
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `${getIcon("spinner", "icon-spin", 16)} Authenticating...`;
    }

    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);
    formData.append("selected_role", selectedRole);
    formData.append("requested_account_type", selectedRole);
    formData.append("requested_role", selectedRole);

    try {
      const data = await API.post(
        `/auth/login?selected_role=${encodeURIComponent(selectedRole)}`,
        formData,
        false
      );

      API.setToken(data.access_token);
      store.setState({ user: data.user, activeOrgId: data.active_org_id });
      showToast(`Welcome back, ${data.user.full_name || 'User'}!`, "success");

      // Critical Rule: Redirect strictly determined by authenticated backend role
      const authenticatedRole = (data.user?.account_type || "STUDENT").toUpperCase();
      if (authenticatedRole === "ADMIN") {
        window.location.hash = "#/admin";
      } else if (authenticatedRole === "MENTOR" || authenticatedRole === "COUNSELOR") {
        window.location.hash = "#/mentor";
      } else {
        window.location.hash = "#/dashboard";
      }
    } catch (err) {
      const msg = err.message || "Authentication failed.";
      if (errorContainer && errorText) {
        errorText.textContent = msg;
        errorContainer.style.display = "flex";
      }
      showToast(msg, "danger");
      if (passwordInput) passwordInput.focus();
    } finally {
      isSubmitting = false;
      if (submitBtn) {
        submitBtn.disabled = false;
        const currentRoleMeta = SELECTABLE_ACCOUNT_ROLES.find(r => r.roleKey === form.getAttribute("data-selected-role")) || SELECTABLE_ACCOUNT_ROLES[0];
        submitBtn.textContent = `Sign In as ${currentRoleMeta.title}`;
      }
    }
  };
}

/**
 * 3. STUDENT REGISTRATION VIEW
 */
export function renderRegister() {
  return `
    <div class="auth-card card" style="max-width: 480px; margin: 2rem auto; padding: 2rem;">
      <div style="text-align: center; margin-bottom: 1.5rem;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 12px; background: rgba(16, 185, 129, 0.12); color: #10b981; margin-bottom: 0.75rem;">
          ${getIcon("graduation-cap", "", 24)}
        </div>
        <h2 style="margin: 0; color: var(--text-primary); font-size: 1.4rem; font-weight: 700;">Student Registration</h2>
        <p style="color: var(--text-secondary); margin-top: 0.25rem; font-size: 0.85rem;">
          Create your student account to build your career profile, parse resumes, and match job opportunities.
        </p>
      </div>

      <form id="student-register-form" novalidate>
        <div class="form-group" style="margin-bottom: 1rem;">
          <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">Full Name *</label>
          <input type="text" id="reg-name" required placeholder="Vinay Nalavade" class="form-input" style="width: 100%;">
        </div>

        <div class="form-group" style="margin-bottom: 1rem;">
          <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">Email Address *</label>
          <input type="email" id="reg-email" required placeholder="student@example.com" class="form-input" style="width: 100%;">
        </div>

        <div class="form-group" style="margin-bottom: 1rem;">
          <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">Password *</label>
          <input type="password" id="reg-password" required minlength="6" placeholder="••••••••" class="form-input" style="width: 100%;">
          <div id="reg-password-strength-container" style="display: none; margin-top: 0.5rem;"></div>
        </div>

        <div class="form-group" style="margin-bottom: 1.5rem;">
          <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">Confirm Password *</label>
          <input type="password" id="reg-confirm-password" required minlength="6" placeholder="••••••••" class="form-input" style="width: 100%;">
        </div>

        <button type="submit" id="reg-submit-btn" class="btn btn-primary" style="width: 100%; justify-content: center; gap: 0.5rem; padding: 0.65rem 1rem;">
          Register as Student
        </button>
      </form>

      <p style="text-align: center; margin-top: 1.5rem; font-size: 0.875rem; color: var(--text-secondary); border-top: 1px solid var(--border-color); padding-top: 1.25rem;">
        Already registered? <a href="#/login?role=student" style="color: var(--primary-color); font-weight: 600;">Sign In as Student</a>
      </p>
    </div>
  `;
}

export function initRegisterListeners() {
  const form = document.getElementById("student-register-form");
  if (!form) return;

  const nameInput = document.getElementById("reg-name");
  const emailInput = document.getElementById("reg-email");
  const passwordInput = document.getElementById("reg-password");
  const confirmInput = document.getElementById("reg-confirm-password");
  const strengthContainer = document.getElementById("reg-password-strength-container");
  const submitBtn = document.getElementById("reg-submit-btn");

  initPasswordToggle(form);

  if (passwordInput && strengthContainer) {
    initPasswordStrengthIndicator(passwordInput, strengthContainer);
  }

  let isSubmitting = false;

  form.onsubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    const full_name = (nameInput?.value || "").trim();
    const email = (emailInput?.value || "").trim();
    const password = passwordInput?.value || "";
    const confirmPassword = confirmInput?.value || "";

    if (!full_name || !email || !password || !confirmPassword) {
      showToast("Please complete all required fields.", "danger");
      return;
    }
    if (!validateFullName(full_name)) {
      showToast("Please enter a valid full name.", "danger");
      nameInput?.focus();
      return;
    }
    if (!validateEmail(email)) {
      showToast("Please enter a valid email address.", "danger");
      emailInput?.focus();
      return;
    }
    if (password.length < 6) {
      showToast("Password must be at least 6 characters.", "danger");
      passwordInput?.focus();
      return;
    }
    if (password !== confirmPassword) {
      showToast("Passwords do not match.", "danger");
      confirmInput?.focus();
      return;
    }

    isSubmitting = true;
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `${getIcon("spinner", "icon-spin", 16)} Registering...`;
    }

    try {
      const data = await API.post("/auth/register", { full_name, email, password, account_type: "STUDENT" });
      API.setToken(data.access_token);
      store.setState({ user: data.user, activeOrgId: data.active_org_id });
      showToast("Student account created successfully! Welcome to NxtMov.", "success");
      window.location.hash = "#/dashboard";
    } catch (err) {
      showToast(err.message || "Registration failed.", "danger");
    } finally {
      isSubmitting = false;
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = "Register as Student";
      }
    }
  };
}

/**
 * 4. MENTOR APPLICATION VIEW ("Apply as Mentor")
 */
export function renderApplyMentor() {
  return `
    <div class="auth-card card" style="max-width: 580px; margin: 2rem auto; padding: 2rem;">
      <div style="text-align: center; margin-bottom: 1.5rem;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 12px; background: rgba(168, 85, 247, 0.12); color: #a855f7; margin-bottom: 0.75rem;">
          ${getIcon("mentor", "", 24)}
        </div>
        <h2 style="margin: 0; color: var(--text-primary); font-size: 1.4rem; font-weight: 700;">Apply as a Mentor</h2>
        <p style="color: var(--text-secondary); margin-top: 0.25rem; font-size: 0.85rem;">
          Submit your academic/institutional details for review. An administrator will review and activate your mentor account.
        </p>
      </div>

      <div id="mentor-app-status-box" style="display: none; margin-bottom: 1.25rem; padding: 1rem; border-radius: var(--radius-md); background: rgba(16, 185, 129, 0.1); border: 1px solid var(--accent-color); color: var(--accent-color); font-size: 0.875rem;"></div>

      <form id="mentor-apply-form" novalidate>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
          <div class="form-group">
            <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">Full Name *</label>
            <input type="text" id="mentor-name" required placeholder="Dr. Ramesh Kulkarni" class="form-input" style="width: 100%;">
          </div>
          <div class="form-group">
            <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">Official Institutional Email *</label>
            <input type="email" id="mentor-email" required placeholder="ramesh@iitb.ac.in" class="form-input" style="width: 100%;">
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
          <div class="form-group">
            <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">Institute / University Name *</label>
            <input type="text" id="mentor-institute" required placeholder="IIT Bombay" class="form-input" style="width: 100%;">
          </div>
          <div class="form-group">
            <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">Employee / Faculty ID *</label>
            <input type="text" id="mentor-emp-id" required placeholder="FAC-2024-098" class="form-input" style="width: 100%;">
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
          <div class="form-group">
            <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">Department *</label>
            <input type="text" id="mentor-department" required placeholder="Computer Science & Engg" class="form-input" style="width: 100%;">
          </div>
          <div class="form-group">
            <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">Designation *</label>
            <input type="text" id="mentor-designation" required placeholder="Associate Professor" class="form-input" style="width: 100%;">
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem;">
          <div class="form-group">
            <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">Password *</label>
            <input type="password" id="mentor-password" required minlength="6" placeholder="••••••••" class="form-input" style="width: 100%;">
          </div>
          <div class="form-group">
            <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">Confirm Password *</label>
            <input type="password" id="mentor-confirm-password" required minlength="6" placeholder="••••••••" class="form-input" style="width: 100%;">
          </div>
        </div>

        <button type="submit" id="mentor-submit-btn" class="btn btn-primary" style="width: 100%; justify-content: center; gap: 0.5rem; padding: 0.65rem 1rem; background: #a855f7; border-color: #a855f7;">
          Submit Mentor Application
        </button>
      </form>

      <p style="text-align: center; margin-top: 1.5rem; font-size: 0.875rem; color: var(--text-secondary); border-top: 1px solid var(--border-color); padding-top: 1.25rem;">
        Already approved? <a href="#/login?role=mentor" style="color: #a855f7; font-weight: 600;">Mentor Login</a>
      </p>
    </div>
  `;
}

export function initApplyMentorListeners() {
  const form = document.getElementById("mentor-apply-form");
  if (!form) return;

  const nameInput = document.getElementById("mentor-name");
  const emailInput = document.getElementById("mentor-email");
  const instInput = document.getElementById("mentor-institute");
  const empIdInput = document.getElementById("mentor-emp-id");
  const deptInput = document.getElementById("mentor-department");
  const desigInput = document.getElementById("mentor-designation");
  const passInput = document.getElementById("mentor-password");
  const confInput = document.getElementById("mentor-confirm-password");
  const submitBtn = document.getElementById("mentor-submit-btn");
  const statusBox = document.getElementById("mentor-app-status-box");

  initPasswordToggle(form);

  let isSubmitting = false;

  form.onsubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    const full_name = (nameInput?.value || "").trim();
    const official_email = (emailInput?.value || "").trim();
    const institute_name = (instInput?.value || "").trim();
    const employee_id = (empIdInput?.value || "").trim();
    const department = (deptInput?.value || "").trim();
    const designation = (desigInput?.value || "").trim();
    const password = passInput?.value || "";
    const confirmPassword = confInput?.value || "";

    if (!full_name || !official_email || !institute_name || !employee_id || !department || !designation || !password) {
      showToast("Please complete all required fields.", "danger");
      return;
    }
    if (!validateEmail(official_email)) {
      showToast("Please enter a valid official email address.", "danger");
      emailInput?.focus();
      return;
    }
    if (password.length < 6) {
      showToast("Password must be at least 6 characters.", "danger");
      passInput?.focus();
      return;
    }
    if (password !== confirmPassword) {
      showToast("Passwords do not match.", "danger");
      confInput?.focus();
      return;
    }

    isSubmitting = true;
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `${getIcon("spinner", "icon-spin", 16)} Submitting Application...`;
    }

    try {
      const res = await API.post("/auth/apply-mentor", {
        full_name,
        official_email,
        institute_name,
        employee_id,
        department,
        designation,
        password
      });

      if (statusBox) {
        statusBox.innerHTML = `
          <strong>✓ Application Submitted!</strong><br>
          ${res.message || 'Your application is under administrator review. You will be able to log in once approved.'}
        `;
        statusBox.style.display = "block";
      }
      showToast("Mentor application submitted for administrator approval.", "success");
      form.reset();
    } catch (err) {
      showToast(err.message || "Failed to submit mentor application.", "danger");
    } finally {
      isSubmitting = false;
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = "Submit Mentor Application";
      }
    }
  };
}

/**
 * 5. ADMINISTRATOR BOOTSTRAP VIEW
 */
export function renderAdminBootstrap() {
  return `
    <div class="auth-card card" style="max-width: 480px; margin: 2rem auto; padding: 2rem;">
      <div style="text-align: center; margin-bottom: 1.5rem;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 12px; background: rgba(239, 68, 68, 0.12); color: #ef4444; margin-bottom: 0.75rem;">
          ${getIcon("shield-check", "", 24)}
        </div>
        <h2 style="margin: 0; color: var(--text-primary); font-size: 1.4rem; font-weight: 700;">Administrator Bootstrap</h2>
        <p style="color: var(--text-secondary); margin-top: 0.25rem; font-size: 0.85rem;">
          Enter the backend server bootstrap secret to provision or initialize the primary Administrator account.
        </p>
      </div>

      <form id="admin-bootstrap-form" novalidate>
        <div class="form-group" style="margin-bottom: 1rem;">
          <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">Server Bootstrap Secret *</label>
          <input type="password" id="boot-key" required placeholder="Enter backend bootstrap secret" class="form-input" style="width: 100%;">
        </div>

        <div class="form-group" style="margin-bottom: 1rem;">
          <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">Administrator Full Name *</label>
          <input type="text" id="boot-name" required placeholder="System Administrator" class="form-input" style="width: 100%;">
        </div>

        <div class="form-group" style="margin-bottom: 1rem;">
          <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">Administrator Email *</label>
          <input type="email" id="boot-email" required placeholder="admin@nxtmov.local" class="form-input" style="width: 100%;">
        </div>

        <div class="form-group" style="margin-bottom: 1.5rem;">
          <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">Password *</label>
          <input type="password" id="boot-password" required minlength="6" placeholder="••••••••" class="form-input" style="width: 100%;">
        </div>

        <button type="submit" id="boot-submit-btn" class="btn btn-primary" style="width: 100%; justify-content: center; gap: 0.5rem; padding: 0.65rem 1rem; background: #ef4444; border-color: #ef4444;">
          Bootstrap Administrator
        </button>
      </form>

      <p style="text-align: center; margin-top: 1.5rem; font-size: 0.875rem; color: var(--text-secondary); border-top: 1px solid var(--border-color); padding-top: 1.25rem;">
        Return to <a href="#/login?role=admin" style="color: #ef4444; font-weight: 600;">Administrator Login</a>
      </p>
    </div>
  `;
}

export function initAdminBootstrapListeners() {
  const form = document.getElementById("admin-bootstrap-form");
  if (!form) return;

  const keyInput = document.getElementById("boot-key");
  const nameInput = document.getElementById("boot-name");
  const emailInput = document.getElementById("boot-email");
  const passInput = document.getElementById("boot-password");
  const submitBtn = document.getElementById("boot-submit-btn");

  initPasswordToggle(form);

  let isSubmitting = false;

  form.onsubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    const bootstrap_key = (keyInput?.value || "").trim();
    const full_name = (nameInput?.value || "").trim();
    const email = (emailInput?.value || "").trim();
    const password = passInput?.value || "";

    if (!bootstrap_key || !full_name || !email || !password) {
      showToast("Please fill in all bootstrap fields.", "danger");
      return;
    }

    isSubmitting = true;
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `${getIcon("spinner", "icon-spin", 16)} Provisioning Admin...`;
    }

    try {
      const data = await API.post("/auth/admin/bootstrap", {
        bootstrap_key,
        full_name,
        email,
        password
      });

      API.setToken(data.access_token);
      store.setState({ user: data.user, activeOrgId: data.active_org_id });
      showToast("Administrator account initialized successfully!", "success");
      window.location.hash = "#/dashboard";
    } catch (err) {
      showToast(err.message || "Administrator bootstrap failed. Verify secret key.", "danger");
    } finally {
      isSubmitting = false;
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = "Bootstrap Administrator";
      }
    }
  };
}

/**
 * Checks public authentication configuration on backend.
 */
async function loadDemoModeConfig() {
  const container = document.getElementById("demo-credentials-container");
  if (!container) return;

  try {
    const config = await API.get("/auth/config");
    if (!config.demo_mode) {
      container.style.display = "none";
    } else {
      const emailElem = document.getElementById("demo-email-text");
      const passElem = document.getElementById("demo-pass-text");
      if (emailElem && config.demo_email) emailElem.textContent = config.demo_email;
      if (passElem && config.demo_password) passElem.textContent = config.demo_password;
    }
  } catch (err) {
    // Non-critical fallback
  }
}

export function renderVerifyEmail() {
  return `
    <div class="card" style="max-width: 440px; margin: 3.5rem auto; padding: 2.25rem; text-align: center;">
      <div style="margin-bottom: 1.5rem;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; border-radius: 50%; background: var(--bg-secondary); color: var(--primary-color); margin-bottom: 1rem;">
          ${getIcon("mail", "", 28)}
        </div>
        <h2 style="font-size: 1.35rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.5rem;">Email Verification</h2>
        <p id="verify-email-status-text" style="color: var(--text-secondary); font-size: 0.875rem; line-height: 1.5;">
          Confirming your email address...
        </p>
      </div>

      <div id="verify-email-action-container" style="display: none; margin-top: 1.5rem;">
        <a href="#/profile" class="btn btn-primary" style="width: 100%; justify-content: center;">
          Go to Profile
        </a>
      </div>
    </div>
  `;
}

export async function initVerifyEmailListeners() {
  const hash = window.location.hash;
  const statusText = document.getElementById("verify-email-status-text");
  const actionContainer = document.getElementById("verify-email-action-container");

  let token = null;
  if (hash.includes("?")) {
    const params = new URLSearchParams(hash.split("?")[1]);
    token = params.get("token");
  }
  if (!token && window.location.search) {
    const params = new URLSearchParams(window.location.search);
    token = params.get("token");
  }

  if (!token) {
    if (statusText) statusText.textContent = "This verification link is invalid or has already been used.";
    if (actionContainer) actionContainer.style.display = "block";
    return;
  }

  try {
    const res = await API.post("/auth/verify-email/confirm", { token });
    if (statusText) {
      statusText.innerHTML = `<span style="color: var(--success-color); font-weight: 600;">✓ ${res.message || 'Email verified successfully!'}</span>`;
    }
    showToast(res.message || "Email verified successfully!", "success");
  } catch (err) {
    const errMsg = err.message || "This verification link has expired. Please request a new one.";
    if (statusText) {
      statusText.innerHTML = `<span style="color: var(--danger-color); font-weight: 500;">${errMsg}</span>`;
    }
    showToast(errMsg, "danger");
  } finally {
    if (actionContainer) actionContainer.style.display = "block";
  }
}

/**
 * 6. FORGOT PASSWORD VIEW
 */
export function renderForgotPassword() {
  return `
    <div class="auth-card card" style="max-width: 460px; margin: 3rem auto; padding: 2.25rem 2rem; border-radius: var(--radius-xl); box-shadow: var(--shadow-lg);">
      <div style="text-align: center; margin-bottom: 1.5rem;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 48px; height: 48px; border-radius: 14px; background: rgba(79, 70, 229, 0.1); color: var(--primary-color); margin-bottom: 0.75rem;">
          ${getIcon("lock", "", 24)}
        </div>
        <h2 style="margin: 0 0 0.35rem 0; color: var(--text-primary); font-size: 1.4rem; font-weight: 700;">
          Reset Your Password
        </h2>
        <p style="color: var(--text-muted); margin: 0; font-size: 0.85rem; line-height: 1.4;">
          Enter your registered email address and we'll send you instructions to reset your password.
        </p>
      </div>

      <div id="forgot-status-box" style="display: none; margin-bottom: 1.25rem; padding: 0.85rem 1rem; border-radius: var(--radius-md); font-size: 0.85rem; line-height: 1.4;"></div>

      <form id="forgot-password-form" novalidate>
        <div class="form-group" style="margin-bottom: 1.25rem;">
          <label style="display: block; margin-bottom: 0.45rem; font-size: 0.85rem; font-weight: 600; color: var(--text-primary);">Email Address *</label>
          <div style="position: relative;">
            <input
              type="email"
              id="forgot-email"
              required
              placeholder="user@example.com"
              class="form-input"
              style="width: 100%; padding-left: 2.25rem;"
              autocomplete="email"
            >
            <span style="position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none;">
              ${getIcon("mail", "", 16)}
            </span>
          </div>
        </div>

        <button
          type="submit"
          id="forgot-submit-btn"
          class="btn btn-primary"
          style="width: 100%; justify-content: center; gap: 0.5rem; padding: 0.65rem 1rem; font-weight: 600; font-size: 0.9rem;"
        >
          Send Password Reset Link
        </button>
      </form>

      <div style="text-align: center; margin-top: 1.5rem; font-size: 0.825rem; color: var(--text-secondary); border-top: 1px solid var(--border-color); padding-top: 1.25rem;">
        Remember your password? <a href="#/login" style="color: var(--primary-color); font-weight: 600;">Return to Sign In</a>
      </div>
    </div>
  `;
}

export function initForgotPasswordListeners() {
  const form = document.getElementById("forgot-password-form");
  if (!form) return;

  const emailInput = document.getElementById("forgot-email");
  const submitBtn = document.getElementById("forgot-submit-btn");
  const statusBox = document.getElementById("forgot-status-box");

  let isSubmitting = false;

  form.onsubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    const email = (emailInput?.value || "").trim();
    if (!email) {
      showToast("Please enter your email address.", "danger");
      emailInput?.focus();
      return;
    }

    isSubmitting = true;
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `${getIcon("spinner", "icon-spin", 16)} Sending Link...`;
    }

    try {
      const res = await API.post("/auth/forgot-password", { email });
      if (statusBox) {
        statusBox.style.display = "block";
        statusBox.style.background = "rgba(16, 185, 129, 0.1)";
        statusBox.style.border = "1px solid var(--success-color)";
        statusBox.style.color = "var(--success-color)";
        statusBox.innerHTML = `<strong>✓ Link Sent!</strong><br>${res.message || 'If an account with this email exists, a password reset link has been sent.'}`;
      }
      showToast(res.message || "Password reset link sent.", "success");
      form.reset();
    } catch (err) {
      showToast(err.message || "Failed to process password reset request.", "danger");
    } finally {
      isSubmitting = false;
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = "Send Password Reset Link";
      }
    }
  };
}

/**
 * 7. RESET PASSWORD VIEW
 */
export function renderResetPassword() {
  return `
    <div class="auth-card card" style="max-width: 460px; margin: 3rem auto; padding: 2.25rem 2rem; border-radius: var(--radius-xl); box-shadow: var(--shadow-lg);">
      <div style="text-align: center; margin-bottom: 1.5rem;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 48px; height: 48px; border-radius: 14px; background: rgba(79, 70, 229, 0.1); color: var(--primary-color); margin-bottom: 0.75rem;">
          ${getIcon("lock", "", 24)}
        </div>
        <h2 style="margin: 0 0 0.35rem 0; color: var(--text-primary); font-size: 1.4rem; font-weight: 700;">
          Set New Password
        </h2>
        <p style="color: var(--text-muted); margin: 0; font-size: 0.85rem; line-height: 1.4;">
          Choose a new password for your account.
        </p>
      </div>

      <div id="reset-status-box" style="display: none; margin-bottom: 1.25rem; padding: 0.85rem 1rem; border-radius: var(--radius-md); font-size: 0.85rem; line-height: 1.4;"></div>

      <form id="reset-password-form" novalidate>
        <div class="form-group" style="margin-bottom: 1rem;">
          <label style="display: block; margin-bottom: 0.45rem; font-size: 0.85rem; font-weight: 600; color: var(--text-primary);">New Password *</label>
          <div style="position: relative;">
            <input
              type="password"
              id="reset-new-password"
              required
              minlength="6"
              placeholder="••••••••"
              class="form-input"
              style="width: 100%; padding-left: 2.25rem;"
            >
            <span style="position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none;">
              ${getIcon("lock", "", 16)}
            </span>
          </div>
          <div id="reset-password-strength-container" style="display: none; margin-top: 0.5rem;"></div>
        </div>

        <div class="form-group" style="margin-bottom: 1.5rem;">
          <label style="display: block; margin-bottom: 0.45rem; font-size: 0.85rem; font-weight: 600; color: var(--text-primary);">Confirm New Password *</label>
          <div style="position: relative;">
            <input
              type="password"
              id="reset-confirm-password"
              required
              minlength="6"
              placeholder="••••••••"
              class="form-input"
              style="width: 100%; padding-left: 2.25rem;"
            >
            <span style="position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none;">
              ${getIcon("lock", "", 16)}
            </span>
          </div>
        </div>

        <button
          type="submit"
          id="reset-submit-btn"
          class="btn btn-primary"
          style="width: 100%; justify-content: center; gap: 0.5rem; padding: 0.65rem 1rem; font-weight: 600; font-size: 0.9rem;"
        >
          Update Password
        </button>
      </form>

      <div style="text-align: center; margin-top: 1.5rem; font-size: 0.825rem; color: var(--text-secondary); border-top: 1px solid var(--border-color); padding-top: 1.25rem;">
        <a href="#/login" style="color: var(--primary-color); font-weight: 600;">Return to Sign In</a>
      </div>
    </div>
  `;
}

export function initResetPasswordListeners() {
  const form = document.getElementById("reset-password-form");
  if (!form) return;

  const newPassInput = document.getElementById("reset-new-password");
  const confPassInput = document.getElementById("reset-confirm-password");
  const strengthContainer = document.getElementById("reset-password-strength-container");
  const submitBtn = document.getElementById("reset-submit-btn");
  const statusBox = document.getElementById("reset-status-box");

  initPasswordToggle(form);

  if (newPassInput && strengthContainer) {
    initPasswordStrengthIndicator(newPassInput, strengthContainer);
  }

  // Extract token from URL hash or query params
  let token = "";
  const hash = window.location.hash;
  if (hash.includes("?")) {
    const params = new URLSearchParams(hash.split("?")[1]);
    token = params.get("token") || "";
  }
  if (!token && window.location.search) {
    const params = new URLSearchParams(window.location.search);
    token = params.get("token") || "";
  }

  if (!token) {
    if (statusBox) {
      statusBox.style.display = "block";
      statusBox.style.background = "rgba(239, 68, 68, 0.1)";
      statusBox.style.border = "1px solid var(--danger-color)";
      statusBox.style.color = "var(--danger-color)";
      statusBox.innerHTML = "<strong>Invalid Reset Link</strong><br>Missing or invalid password reset token. Please request a new password reset link.";
    }
    if (submitBtn) submitBtn.disabled = true;
    return;
  }

  let isSubmitting = false;

  form.onsubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    const new_password = newPassInput?.value || "";
    const confirm_password = confPassInput?.value || "";

    if (!new_password || !confirm_password) {
      showToast("Please complete all password fields.", "danger");
      return;
    }
    if (new_password.length < 6) {
      showToast("Password must be at least 6 characters.", "danger");
      newPassInput?.focus();
      return;
    }
    if (new_password !== confirm_password) {
      showToast("Passwords do not match.", "danger");
      confPassInput?.focus();
      return;
    }

    isSubmitting = true;
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `${getIcon("spinner", "icon-spin", 16)} Updating Password...`;
    }

    try {
      const res = await API.post("/auth/reset-password", { token, new_password });
      showToast(res.message || "Password updated successfully!", "success");
      if (statusBox) {
        statusBox.style.display = "block";
        statusBox.style.background = "rgba(16, 185, 129, 0.1)";
        statusBox.style.border = "1px solid var(--success-color)";
        statusBox.style.color = "var(--success-color)";
        statusBox.innerHTML = "<strong>✓ Password Updated!</strong><br>Your password has been changed successfully. Redirecting to sign in...";
      }
      setTimeout(() => {
        window.location.hash = "#/login";
      }, 1500);
    } catch (err) {
      const errMsg = err.message || "This password reset link is invalid or has expired.";
      if (statusBox) {
        statusBox.style.display = "block";
        statusBox.style.background = "rgba(239, 68, 68, 0.1)";
        statusBox.style.border = "1px solid var(--danger-color)";
        statusBox.style.color = "var(--danger-color)";
        statusBox.innerHTML = `<strong>Reset Failed</strong><br>${errMsg}`;
      }
      showToast(errMsg, "danger");
    } finally {
      isSubmitting = false;
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = "Update Password";
      }
    }
  };
}
