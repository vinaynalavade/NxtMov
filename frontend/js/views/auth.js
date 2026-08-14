import { API } from "../api.js";
import { store } from "../store.js";
import { showToast, initPasswordToggle } from "../components.js";

export function renderLogin() {
  return `
    <div class="auth-card card" style="max-width: 440px; margin: 3rem auto;">
      <h2 style="text-align: center; margin-bottom: 0.5rem;">Log in to NxtMov</h2>
      <p style="text-align: center; color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.875rem;">
        Enter your credentials to access your personal job-search workspace.
      </p>

      <!-- REMOVE BEFORE PRODUCTION DEPLOYMENT: Demo Mode Card Container -->
      <div id="demo-credentials-container" style="margin-bottom: 1.25rem;">
        <div style="background-color: var(--bg-secondary); border: 1px solid var(--border-color); border-left: 4px solid var(--warning-color); border-radius: var(--radius-md); padding: 1rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 0.75rem; font-weight: 700; color: var(--warning-color); letter-spacing: 0.5px;">
              ⚡ DEVELOPMENT / DEMO MODE
            </span>
            <span class="badge-status badge-warning" style="font-size: 0.65rem;">DEV ONLY</span>
          </div>

          <div style="font-size: 0.825rem; color: var(--text-secondary); margin-bottom: 0.75rem;">
            <div><strong>Email:</strong> <code id="demo-email-text">demo@nxtmov.local</code></div>
            <div><strong>Password:</strong> <code id="demo-pass-text">NxtMov@123</code></div>
          </div>

          <button type="button" id="use-demo-creds-btn" class="btn btn-outline" style="width: 100%; font-size: 0.8rem; padding: 0.35rem 0.6rem; color: var(--primary-color); border-color: var(--primary-color);">
            ⚡ Use Demo Account
          </button>
        </div>
      </div>

      <form id="login-form">
        <div class="form-group" style="margin-bottom: 1rem;">
          <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; font-weight: 500;">Email Address</label>
          <input type="email" id="login-email" required placeholder="you@example.com" class="form-input" style="width: 100%;">
        </div>

        <div class="form-group" style="margin-bottom: 1.5rem;">
          <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; font-weight: 500;">Password</label>
          <input type="password" id="login-password" required placeholder="••••••••" class="form-input" style="width: 100%;">
        </div>

        <button type="submit" class="btn btn-primary" style="width: 100%;">Log In</button>
      </form>

      <p style="text-align: center; margin-top: 1.5rem; font-size: 0.875rem; color: var(--text-secondary);">
        Don't have an account? <a href="#/register" style="color: var(--primary-color);">Create Workspace</a>
      </p>
    </div>
  `;
}

export function initLoginListeners() {
  const form = document.getElementById("login-form");
  if (!form) return;

  // Attach password visibility eye toggle
  initPasswordToggle(form);

  // Attach Use Demo Account button handler immediately
  const demoBtn = document.getElementById("use-demo-creds-btn");
  if (demoBtn) {
    demoBtn.onclick = (e) => {
      e.preventDefault();
      const emailText = document.getElementById("demo-email-text")?.textContent || "demo@nxtmov.local";
      const passText = document.getElementById("demo-pass-text")?.textContent || "NxtMov@123";
      
      const emailInput = document.getElementById("login-email");
      const passwordInput = document.getElementById("login-password");
      if (emailInput) emailInput.value = emailText;
      if (passwordInput) passwordInput.value = passText;
      showToast("Demo credentials filled into login form.");
    };
  }

  // Check backend auth config asynchronously
  loadDemoModeConfig();

  form.onsubmit = async (e) => {
    e.preventDefault();
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;

    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);

    try {
      const data = await API.post("/auth/login", formData, false);
      API.setToken(data.access_token);
      store.setState({ user: data.user, activeOrgId: data.active_org_id });
      showToast(`Welcome back, ${data.user.full_name}!`);
      window.location.hash = "#/dashboard";
    } catch (err) {
      showToast(err.message, "danger");
    }
  };
}

/**
 * REMOVE BEFORE PRODUCTION DEPLOYMENT
 * Checks development demo configuration on backend. If demo_mode is disabled, hides Demo Card.
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
    console.warn("Auth config check error:", err);
  }
}

export function renderRegister() {
  return `
    <div class="auth-card card" style="max-width: 450px; margin: 2rem auto;">
      <h2 style="text-align: center; margin-bottom: 0.5rem;">Create NxtMov Account</h2>
      <p style="text-align: center; color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.875rem;">
        Get your personal job-search workspace in seconds.
      </p>

      <form id="register-form">
        <div class="form-group" style="margin-bottom: 1rem;">
          <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; font-weight: 500;">Full Name</label>
          <input type="text" id="reg-name" required placeholder="Vinay Sharma" class="form-input" style="width: 100%;">
        </div>

        <div class="form-group" style="margin-bottom: 1rem;">
          <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; font-weight: 500;">Email Address</label>
          <input type="email" id="reg-email" required placeholder="vinay@example.com" class="form-input" style="width: 100%;">
        </div>

        <div class="form-group" style="margin-bottom: 1.5rem;">
          <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; font-weight: 500;">Password</label>
          <input type="password" id="reg-password" required minlength="8" placeholder="••••••••" class="form-input" style="width: 100%;">
        </div>

        <button type="submit" class="btn btn-primary" style="width: 100%;">Provision Workspace</button>
      </form>

      <p style="text-align: center; margin-top: 1.5rem; font-size: 0.875rem; color: var(--text-secondary);">
        Already registered? <a href="#/login" style="color: var(--primary-color);">Log In</a>
      </p>
    </div>
  `;
}

export function initRegisterListeners() {
  const form = document.getElementById("register-form");
  if (!form) return;

  // Attach password visibility eye toggle
  initPasswordToggle(form);

  form.onsubmit = async (e) => {
    e.preventDefault();
    const full_name = document.getElementById("reg-name").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;

    try {
      const data = await API.post("/auth/register", { full_name, email, password });
      API.setToken(data.access_token);
      store.setState({ user: data.user, activeOrgId: data.active_org_id });
      showToast("Personal workspace provisioned successfully!");
      window.location.hash = "#/dashboard";
    } catch (err) {
      showToast(err.message, "danger");
    }
  };
}
