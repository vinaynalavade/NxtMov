import { API } from "../api.js";
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
 * Publicly selectable account types for initial login screen
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
    description: "Manage your profile, resume, applications and career journey."
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
    description: "Guide students, monitor progress and provide mentorship."
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
    description: "Manage users, workspaces, roles and platform operations."
  },
  {
    roleKey: "RECRUITER",
    urlParam: "recruiter",
    title: "Recruiter",
    badgeLabel: "Talent Partner",
    badgeClass: "badge-recruiter",
    icon: "briefcase",
    accentColor: "#3b82f6",
    accentBg: "rgba(59, 130, 246, 0.12)",
    description: "Manage candidates, jobs, applications and recruitment workflows."
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
 * Displays Account Type Selection if no role is chosen; otherwise renders Role-Specific Login.
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
 * 1. ACCOUNT-TYPE SELECTION SCREEN
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

      <!-- 4 Selectable Role Cards -->
      <div class="role-select-grid" role="group" aria-label="Select your account type">
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

      <div style="text-align: center; margin-top: 1.5rem; padding-top: 1.25rem; border-top: 1px solid var(--border-color); font-size: 0.875rem; color: var(--text-secondary);">
        Don't have an account? <a href="#/register" style="color: var(--primary-color); font-weight: 600;">Create Workspace</a>
      </div>
    </div>
  `;
}

/**
 * 2. ROLE-SPECIFIC LOGIN SCREEN
 */
function renderRoleSpecificLoginScreen(roleMeta) {
  return `
    <div class="auth-card card" style="max-width: 460px; margin: 2.5rem auto; padding: 2rem;">
      <!-- Back Navigation to Change Role -->
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

      <!-- Demo Mode Card Container (if enabled) -->
      <div id="demo-credentials-container" style="margin-bottom: 1.25rem;">
        <div style="background-color: var(--bg-secondary); border: 1px solid var(--border-color); border-left: 4px solid var(--warning-color); border-radius: var(--radius-md); padding: 0.875rem 1rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
            <span style="font-size: 0.725rem; font-weight: 700; color: var(--warning-color); letter-spacing: 0.5px; display: flex; align-items: center; gap: 0.35rem;">
              ${getIcon("sparkles", "", 13)} DEMO & EVALUATION MODE
            </span>
            <span class="badge-status badge-warning" style="font-size: 0.625rem;">DEV ONLY</span>
          </div>

          <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.65rem;">
            <div><strong>Email:</strong> <code id="demo-email-text">demo@nxtmov.local</code></div>
            <div><strong>Password:</strong> <code id="demo-pass-text">NxtMov@123</code></div>
          </div>

          <button type="button" id="use-demo-creds-btn" class="btn btn-outline" style="width: 100%; font-size: 0.775rem; padding: 0.3rem 0.5rem; color: var(--primary-color); border-color: var(--primary-color); gap: 0.35rem; justify-content: center;">
            ${getIcon("user", "", 13)} Fill Demo ${roleMeta.title} Credentials
          </button>
        </div>
      </div>

      <!-- Login Form -->
      <form id="login-form" novalidate data-requested-role="${roleMeta.roleKey}">
        <div class="form-group" style="margin-bottom: 1rem;">
          <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">
            Email Address
          </label>
          <input
            type="email"
            id="login-email"
            required
            placeholder="you@example.com"
            class="form-input"
            style="width: 100%;"
            autocomplete="email"
          >
        </div>

        <div class="form-group" style="margin-bottom: 1.5rem;">
          <label style="display: block; margin-bottom: 0.45rem; font-size: 0.875rem; font-weight: 600;">
            Password
          </label>
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

      <p style="text-align: center; margin-top: 1.5rem; font-size: 0.875rem; color: var(--text-secondary);">
        Don't have an account? <a href="#/register" style="color: var(--primary-color); font-weight: 600;">Create Workspace</a>
      </p>
    </div>
  `;
}

/**
 * Attaches interactive event listeners to /login
 */
export function initLoginListeners() {
  const selectedRoleKey = getSelectedRoleFromHash();

  // If on Account Type Selection Screen: attach card click listeners
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

  // If on Role-Specific Login Screen:
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
  const requestedRole = form.getAttribute("data-requested-role") || selectedRoleKey;

  // Attach password visibility eye toggle
  initPasswordToggle(form);

  // Attach Use Demo Account button handler
  const demoBtn = document.getElementById("use-demo-creds-btn");
  if (demoBtn) {
    demoBtn.onclick = (e) => {
      e.preventDefault();
      const emailText = document.getElementById("demo-email-text")?.textContent || "demo@nxtmov.local";
      const passText = document.getElementById("demo-pass-text")?.textContent || "NxtMov@123";

      if (emailInput) emailInput.value = emailText;
      if (passwordInput) passwordInput.value = passText;
      showToast(`Demo ${requestedRole} credentials filled.`);
      submitBtn?.focus();
    };
  }

  // Check backend auth config asynchronously
  loadDemoModeConfig();

  let isSubmitting = false;

  form.onsubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    const email = (emailInput?.value || "").trim();
    const password = passwordInput?.value || "";

    // Input validations
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

    // Set loading state & disable submission
    isSubmitting = true;
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `${getIcon("spinner", "icon-spin", 16)} Authenticating...`;
    }

    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);
    if (requestedRole) {
      formData.append("requested_role", requestedRole);
    }

    try {
      const data = await API.post(`/auth/login?requested_role=${encodeURIComponent(requestedRole || "")}`, formData, false);
      API.setToken(data.access_token);
      store.setState({ user: data.user, activeOrgId: data.active_org_id });
      showToast("Login successful. Welcome back!", "success");
      window.location.hash = "#/dashboard";
    } catch (err) {
      showToast(err.message || "Authentication failed.", "danger");
      if (passwordInput) {
        passwordInput.focus();
      }
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
 * Checks public authentication configuration on backend. If demo_mode is disabled, hides Demo Card.
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
    // Non-critical fallback for local dev
  }
}

export function renderRegister() {
  return `
    <div class="auth-card card" style="max-width: 450px; margin: 2rem auto;">
      <h2 style="text-align: center; margin-bottom: 0.5rem; color: var(--text-primary);">Create NxtMov Account</h2>
      <p style="text-align: center; color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.875rem;">
        Get your personal career and talent workspace in seconds.
      </p>

      <form id="register-form" novalidate>
        <div class="form-group" style="margin-bottom: 1rem;">
          <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; font-weight: 500;">Full Name *</label>
          <input type="text" id="reg-name" required placeholder="Vinay Nalavade" class="form-input" style="width: 100%;">
        </div>

        <div class="form-group" style="margin-bottom: 1rem;">
          <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; font-weight: 500;">Email Address *</label>
          <input type="email" id="reg-email" required placeholder="vinay@example.com" class="form-input" style="width: 100%;">
        </div>

        <div class="form-group" style="margin-bottom: 1.5rem;">
          <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; font-weight: 500;">Password *</label>
          <input type="password" id="reg-password" required minlength="8" placeholder="••••••••" class="form-input" style="width: 100%;">
          <div id="reg-password-strength-container" style="display: none; margin-top: 0.5rem;"></div>
        </div>

        <button type="submit" id="reg-submit-btn" class="btn btn-primary" style="width: 100%; justify-content: center; gap: 0.5rem;">
          Create Account & Workspace
        </button>
      </form>

      <p style="text-align: center; margin-top: 1.5rem; font-size: 0.875rem; color: var(--text-secondary);">
        Already registered? <a href="#/login" style="color: var(--primary-color); font-weight: 600;">Log In</a>
      </p>
    </div>
  `;
}

export function initRegisterListeners() {
  const form = document.getElementById("register-form");
  if (!form) return;

  const nameInput = document.getElementById("reg-name");
  const emailInput = document.getElementById("reg-email");
  const passwordInput = document.getElementById("reg-password");
  const strengthContainer = document.getElementById("reg-password-strength-container");
  const submitBtn = document.getElementById("reg-submit-btn");

  // Attach password visibility eye toggle
  initPasswordToggle(form);

  // Attach live password strength indicator
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

    // Input validations
    if (!full_name || !email || !password) {
      showToast("Please complete all required fields.", "danger");
      return;
    }
    if (!validateFullName(full_name)) {
      showToast("Please enter a valid full name (letters, spaces, and hyphens only).", "danger");
      nameInput?.focus();
      return;
    }
    if (!validateEmail(email)) {
      showToast("Please enter a valid email address.", "danger");
      emailInput?.focus();
      return;
    }
    if (password.length < 6) {
      showToast("Password does not meet the required security requirements.", "danger");
      passwordInput?.focus();
      return;
    }

    // Set loading state & disable submission
    isSubmitting = true;
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `${getIcon("spinner", "icon-spin", 16)} Provisioning Workspace...`;
    }

    try {
      const data = await API.post("/auth/register", { full_name, email, password });
      API.setToken(data.access_token);
      store.setState({ user: data.user, activeOrgId: data.active_org_id });
      showToast("Account created successfully. Welcome to NxtMov!", "success");
      window.location.hash = "#/dashboard";
    } catch (err) {
      showToast(err.message, "danger");
    } finally {
      isSubmitting = false;
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = "Create Account & Workspace";
      }
    }
  };
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
    const errMsg = normalizeErrorMessage(err, "This verification link has expired. Please request a new one.");
    if (statusText) {
      statusText.innerHTML = `<span style="color: var(--danger-color); font-weight: 500;">${errMsg}</span>`;
    }
    showToast(errMsg, "danger");
  } finally {
    if (actionContainer) actionContainer.style.display = "block";
  }
}
