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
const SELECTABLE_ACCOUNT_ROLES = [
  {
    roleKey: "STUDENT",
    urlParam: "student",
    title: "Student",
    badgeLabel: "Candidate / Talent",
    badgeClass: "badge-student",
    icon: "graduation-cap",
    accentColor: "#10b981",
    accentBg: "rgba(16, 185, 129, 0.12)",
    description: "Manage your profile, resume analysis, matched jobs, and track applications."
  },
  {
    roleKey: "MENTOR",
    urlParam: "mentor",
    title: "Mentor",
    badgeLabel: "Career Guide",
    badgeClass: "badge-mentor",
    icon: "mentor",
    accentColor: "#a855f7",
    accentBg: "rgba(168, 85, 247, 0.12)",
    description: "Guide students, monitor progress, review ATS readiness, and conduct sessions."
  },
  {
    roleKey: "ADMIN",
    urlParam: "admin",
    title: "Administrator",
    badgeLabel: "Workspace Admin",
    badgeClass: "badge-admin",
    icon: "shield-check",
    accentColor: "#ef4444",
    accentBg: "rgba(239, 68, 68, 0.12)",
    description: "Manage users, mentor approvals, organizations, and platform operations."
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
 * Master render function for /login
 */
export function renderLogin() {
  const selectedRoleKey = getSelectedRoleFromHash();

  if (!selectedRoleKey) {
    return renderAccountTypeSelectionScreen();
  }

  const roleMeta = SELECTABLE_ACCOUNT_ROLES.find(r => r.roleKey === selectedRoleKey) || SELECTABLE_ACCOUNT_ROLES[0];
  return renderRoleSpecificLoginScreen(roleMeta);
}

/**
 * 1. ACCOUNT-TYPE SELECTION SCREEN ("How are you using NxtMov?")
 */
function renderAccountTypeSelectionScreen() {
  return `
    <div class="auth-card card" style="max-width: 680px; margin: 2.5rem auto; padding: 2.25rem 2rem;">
      <div style="text-align: center; margin-bottom: 2rem;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 50px; height: 50px; border-radius: 14px; background: rgba(79, 70, 229, 0.1); color: var(--primary-color); margin-bottom: 1rem;">
          ${getIcon("users", "", 26)}
        </div>
        <h2 style="margin-bottom: 0.5rem; color: var(--text-primary); font-size: 1.6rem; font-weight: 800; letter-spacing: -0.02em;">
          How are you using NxtMov?
        </h2>
        <p style="color: var(--text-secondary); font-size: 0.9rem; max-width: 480px; margin: 0 auto; line-height: 1.5;">
          Select your account type to access your tailored workspace, intelligence tools, and dashboard.
        </p>
      </div>

      <!-- 3 Selectable Account Type Cards -->
      <div class="role-select-grid" role="group" aria-label="Select your account type" style="grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));">
        ${SELECTABLE_ACCOUNT_ROLES.map(role => `
          <button
            type="button"
            class="role-select-card"
            data-role-param="${role.urlParam}"
            aria-label="Log in as ${role.title}: ${role.description}"
            tabindex="0"
          >
            <div class="role-select-card-header">
              <div class="role-select-icon-wrapper" style="background: ${role.accentBg}; color: ${role.accentColor};">
                ${getIcon(role.icon, "", 20)}
              </div>
              <span class="role-badge ${role.badgeClass}" style="font-size: 0.65rem;">
                ${role.badgeLabel}
              </span>
            </div>
            <div class="role-select-title">
              <span>${role.title}</span>
              <span style="color: var(--text-muted); font-size: 0.85rem; margin-left: auto;">${getIcon("arrow-right", "", 14)}</span>
            </div>
            <p class="role-select-desc">
              ${role.description}
            </p>
          </button>
        `).join("")}
      </div>

      <div style="text-align: center; margin-top: 1.75rem; padding-top: 1.25rem; border-top: 1px solid var(--border-color); font-size: 0.875rem; color: var(--text-secondary);">
        Need to register? <a href="#/register" style="color: var(--primary-color); font-weight: 600;">Student Sign Up</a> • <a href="#/apply-mentor" style="color: #a855f7; font-weight: 600;">Apply as Mentor</a>
      </div>
    </div>
  `;
}

/**
 * 2. ROLE-SPECIFIC LOGIN SCREEN
 */
function renderRoleSpecificLoginScreen(roleMeta) {
  const isMentor = roleMeta.roleKey === "MENTOR";
  const isAdmin = roleMeta.roleKey === "ADMIN";

  return `
    <div class="auth-card card" style="max-width: 460px; margin: 2.5rem auto; padding: 2rem;">
      <!-- Back Navigation to Change Account Type -->
      <div style="margin-bottom: 1.25rem;">
        <button
          type="button"
          id="btn-change-account-type"
          class="btn btn-ghost"
          style="font-size: 0.825rem; padding: 0.3rem 0.5rem; gap: 0.4rem; color: var(--text-secondary); margin-left: -0.5rem;"
          aria-label="Change account type"
        >
          ${getIcon("arrow-left", "", 14)} <span>Change account type</span>
        </button>
      </div>

      <!-- Role-Specific Header -->
      <div style="text-align: center; margin-bottom: 1.5rem;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 12px; background: ${roleMeta.accentBg}; color: ${roleMeta.accentColor}; margin-bottom: 0.75rem;">
          ${getIcon(roleMeta.icon, "", 22)}
        </div>
        <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem; margin-bottom: 0.25rem;">
          <h2 style="margin: 0; color: var(--text-primary); font-size: 1.4rem; font-weight: 700;">
            ${roleMeta.title} Login
          </h2>
          <span class="role-badge ${roleMeta.badgeClass}" style="font-size: 0.65rem;">
            ${roleMeta.title}
          </span>
        </div>
        <p style="color: var(--text-secondary); margin: 0; font-size: 0.85rem;">
          ${roleMeta.description}
        </p>
      </div>

      <!-- Error / Status Container -->
      <div id="login-error-container" style="display: none; margin-bottom: 1rem; padding: 0.75rem 1rem; border-radius: var(--radius-md); background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger-color); color: var(--danger-color); font-size: 0.85rem;"></div>

      <!-- Demo Credentials Banner (Dev/Evaluation) -->
      <div id="demo-credentials-container" style="margin-bottom: 1.25rem;">
        <div style="background-color: var(--bg-secondary); border: 1px solid var(--border-color); border-left: 4px solid var(--warning-color); border-radius: var(--radius-md); padding: 0.875rem 1rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
            <span style="font-size: 0.725rem; font-weight: 700; color: var(--warning-color); letter-spacing: 0.5px; display: flex; align-items: center; gap: 0.35rem;">
              ${getIcon("sparkles", "", 13)} DEMO & EVALUATION MODE
            </span>
            <span class="badge-status badge-warning" style="font-size: 0.625rem;">DEV ONLY</span>
          </div>
          <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.65rem;">
            <div><strong>Admin Email:</strong> <code id="demo-email-text">demo@nxtmov.local</code></div>
            <div><strong>Password:</strong> <code id="demo-pass-text">NxtMov@123</code></div>
          </div>
          <button type="button" id="use-demo-creds-btn" class="btn btn-outline" style="width: 100%; font-size: 0.775rem; padding: 0.3rem 0.5rem; color: var(--primary-color); border-color: var(--primary-color); gap: 0.35rem; justify-content: center;">
            ${getIcon("user", "", 13)} Fill Demo Credentials
          </button>
        </div>
      </div>

      <!-- Login Form -->
      <form id="login-form" novalidate data-requested-role="${roleMeta.roleKey}">
        <div class="form-group" style="margin-bottom: 1rem;">
          <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">
            ${isMentor ? "Official Email Address *" : "Email Address *"}
          </label>
          <input
            type="email"
            id="login-email"
            required
            placeholder="${isMentor ? 'faculty@institute.edu' : 'you@example.com'}"
            class="form-input"
            style="width: 100%;"
            autocomplete="email"
          >
        </div>

        <div class="form-group" style="margin-bottom: 1.5rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.45rem;">
            <label style="font-size: 0.875rem; font-weight: 600; margin: 0;">Password *</label>
            <a href="#/forgot-password" style="font-size: 0.775rem; color: var(--primary-color);">Forgot?</a>
          </div>
          <input
            type="password"
            id="login-password"
            required
            placeholder="••••••••"
            class="form-input"
            style="width: 100%;"
            autocomplete="current-password"
          >
        </div>

        <button
          type="submit"
          id="login-submit-btn"
          class="btn btn-primary"
          style="width: 100%; justify-content: center; gap: 0.5rem; padding: 0.65rem 1rem;"
        >
          Sign In as ${roleMeta.title}
        </button>
      </form>

      <!-- Context-Aware Bottom Links -->
      <div style="text-align: center; margin-top: 1.5rem; font-size: 0.875rem; color: var(--text-secondary); border-top: 1px solid var(--border-color); padding-top: 1.25rem;">
        ${roleMeta.roleKey === 'STUDENT' ? `
          Don't have an account? <a href="#/register" style="color: var(--primary-color); font-weight: 600;">Register as Student</a>
        ` : roleMeta.roleKey === 'MENTOR' ? `
          Want to join as a mentor? <a href="#/apply-mentor" style="color: #a855f7; font-weight: 600;">Apply as Mentor</a>
        ` : `
          Need initial admin access? <a href="#/admin-bootstrap" style="color: #ef4444; font-weight: 600;">Bootstrap Administrator</a>
        `}
      </div>
    </div>
  `;
}

/**
 * Attaches interactive event listeners to /login
 */
export function initLoginListeners() {
  const selectedRoleKey = getSelectedRoleFromHash();

  if (!selectedRoleKey) {
    const cards = document.querySelectorAll(".role-select-card");
    cards.forEach(card => {
      const selectRole = () => {
        const param = card.getAttribute("data-role-param");
        if (param) {
          window.location.hash = `#/login?role=${param}`;
        }
      };

      card.onclick = selectRole;
      card.onkeydown = (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          selectRole();
        }
      };
    });
    return;
  }

  const changeRoleBtn = document.getElementById("btn-change-account-type");
  if (changeRoleBtn) {
    changeRoleBtn.onclick = (e) => {
      e.preventDefault();
      window.location.hash = "#/login";
    };
  }

  const form = document.getElementById("login-form");
  if (!form) return;

  const emailInput = document.getElementById("login-email");
  const passwordInput = document.getElementById("login-password");
  const submitBtn = document.getElementById("login-submit-btn");
  const errorContainer = document.getElementById("login-error-container");
  const requestedRole = form.getAttribute("data-requested-role") || selectedRoleKey;

  initPasswordToggle(form);

  const demoBtn = document.getElementById("use-demo-creds-btn");
  if (demoBtn) {
    demoBtn.onclick = (e) => {
      e.preventDefault();
      const emailText = document.getElementById("demo-email-text")?.textContent || "demo@nxtmov.local";
      const passText = document.getElementById("demo-pass-text")?.textContent || "NxtMov@123";

      if (emailInput) emailInput.value = emailText;
      if (passwordInput) passwordInput.value = passText;
      showToast("Demo credentials filled.");
      submitBtn?.focus();
    };
  }

  loadDemoModeConfig();

  let isSubmitting = false;

  form.onsubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    const email = (emailInput?.value || "").trim();
    const password = passwordInput?.value || "";

    if (errorContainer) errorContainer.style.display = "none";

    if (!email) {
      showToast("Please enter your email address.", "danger");
      emailInput?.focus();
      return;
    }
    if (!password) {
      showToast("Please enter your password.", "danger");
      passwordInput?.focus();
      return;
    }
    if (!validateEmail(email)) {
      showToast("Please enter a valid email address.", "danger");
      emailInput?.focus();
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
    formData.append("requested_account_type", requestedRole);
    formData.append("requested_role", requestedRole);

    try {
      const data = await API.post(
        `/auth/login?requested_account_type=${encodeURIComponent(requestedRole || "")}`,
        formData,
        false
      );

      API.setToken(data.access_token);
      store.setState({ user: data.user, activeOrgId: data.active_org_id });
      showToast(`Welcome, ${data.user.full_name || 'User'}!`, "success");
      window.location.hash = "#/dashboard";
    } catch (err) {
      const msg = err.message || "Authentication failed.";
      if (errorContainer) {
        errorContainer.textContent = msg;
        errorContainer.style.display = "block";
      }
      showToast(msg, "danger");
      if (passwordInput) passwordInput.focus();
    } finally {
      isSubmitting = false;
      if (submitBtn) {
        submitBtn.disabled = false;
        const roleMeta = SELECTABLE_ACCOUNT_ROLES.find(r => r.roleKey === requestedRole);
        submitBtn.innerHTML = `Sign In as ${roleMeta ? roleMeta.title : 'User'}`;
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
