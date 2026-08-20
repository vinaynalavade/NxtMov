import { normalizeErrorMessage } from "./api.js";
import { getIcon } from "./icons.js";

/* ================================================================
   TOAST NOTIFICATIONS — Single source of truth
   ================================================================ */
const MAX_TOASTS = 4;
const TOAST_DURATION = 4000;
let lastToastMessage = "";
let lastToastTimestamp = 0;

export function showToast(message, type = "success") {
  const cleanMessage = normalizeErrorMessage(message);
  if (!cleanMessage) return;

  const now = Date.now();
  // Debounce identical toast messages within 2 seconds
  if (cleanMessage === lastToastMessage && (now - lastToastTimestamp) < 2000) {
    return;
  }
  lastToastMessage = cleanMessage;
  lastToastTimestamp = now;

  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  // Prevent duplicate toasts currently in the DOM
  const existing = container.querySelectorAll(".toast");
  for (const t of existing) {
    if (t.dataset.msg === cleanMessage) return;
  }

  // Cap max visible toasts
  while (container.children.length >= MAX_TOASTS) {
    removeToast(container.firstChild);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.dataset.msg = cleanMessage;

  const iconName = type === "success" ? "check-circle" : type === "danger" ? "alert-circle" : type === "warning" ? "alert" : "info";
  toast.innerHTML = `
    <div style="display: flex; align-items: center; gap: 0.5rem; flex: 1;">
      <span class="toast-icon">${getIcon(iconName, "", 16)}</span>
      <span style="font-size: 0.85rem; font-weight: 500;">${cleanMessage}</span>
    </div>
    <button class="toast-close" aria-label="Dismiss">&times;</button>
  `;

  let timer = null;
  const dismiss = () => {
    if (timer) clearTimeout(timer);
    removeToast(toast);
  };

  toast.querySelector(".toast-close").addEventListener("click", dismiss);
  container.appendChild(toast);

  timer = setTimeout(() => {
    removeToast(toast);
  }, TOAST_DURATION);
}

function removeToast(toast) {
  if (!toast || !toast.parentNode) return;
  toast.style.opacity = "0";
  toast.style.transform = "translateY(8px)";
  setTimeout(() => {
    if (toast && toast.parentNode) toast.remove();
  }, 150);
}

/* ================================================================
   MODAL — Single source of truth
   ================================================================ */
export function createModal(title, htmlContent) {
  // Clean up any existing modal
  const existingOverlay = document.getElementById("modal-overlay");
  if (existingOverlay) existingOverlay.remove();

  const modalOverlay = document.createElement("div");
  modalOverlay.id = "modal-overlay";
  modalOverlay.className = "modal-overlay";
  document.body.appendChild(modalOverlay);

  modalOverlay.innerHTML = `
    <div class="modal-card">
      <div class="modal-header">
        <h3 style="margin: 0; font-size: 1.1rem; font-weight: 700; color: var(--text-primary);">${title}</h3>
        <button class="modal-close" aria-label="Close" style="background: none; border: none; font-size: 1.25rem; cursor: pointer; color: var(--text-muted);">&times;</button>
      </div>
      <div class="modal-body">
        ${htmlContent}
      </div>
    </div>
  `;

  modalOverlay.style.display = "flex";

  const closeModal = () => {
    modalOverlay.style.display = "none";
    setTimeout(() => modalOverlay.remove(), 100);
  };

  const closeBtn = modalOverlay.querySelector(".modal-close");
  if (closeBtn) closeBtn.addEventListener("click", closeModal);

  modalOverlay.querySelectorAll(".close-modal-btn").forEach((btn) => {
    btn.addEventListener("click", closeModal);
  });

  modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) closeModal();
  });

  const escHandler = (e) => {
    if (e.key === "Escape") {
      closeModal();
      document.removeEventListener("keydown", escHandler);
    }
  };
  document.addEventListener("keydown", escHandler);

  return { closeModal, modalOverlay };
}

export function openModal(title, htmlContent, onConfirm = null) {
  const { closeModal, modalOverlay } = createModal(title, htmlContent);

  if (onConfirm) {
    const body = modalOverlay.querySelector(".modal-body");
    const footer = document.createElement("div");
    footer.className = "modal-footer";
    footer.innerHTML = `
      <button class="btn btn-outline cancel-btn">Cancel</button>
      <button class="btn btn-primary confirm-btn">Submit</button>
    `;
    body.appendChild(footer);

    footer.querySelector(".cancel-btn").addEventListener("click", closeModal);
    footer.querySelector(".confirm-btn").addEventListener("click", () => {
      onConfirm(closeModal);
    });
  }
}

/* ================================================================
   STATUS BADGES
   ================================================================ */
export function formatBadge(status) {
  const map = {
    NOT_CONTACTED: { label: "Not Contacted", class: "badge-muted" },
    CONTACTED: { label: "Contacted", class: "badge-info" },
    INTERESTED: { label: "Interested", class: "badge-success" },
    KEEP_IN_TOUCH: { label: "Keep in Touch", class: "badge-warning" },
    OPPORTUNITY_AVAILABLE: { label: "Opportunity Available", class: "badge-accent" },
    NOT_RELEVANT: { label: "Not Relevant", class: "badge-danger" },
    DO_NOT_CONTACT: { label: "Do Not Contact", class: "badge-danger" },
    PENDING: { label: "Pending", class: "badge-warning" },
    COMPLETED: { label: "Completed", class: "badge-success" },
    APPLIED: { label: "Applied", class: "badge-info" },
    SUBMITTED: { label: "Submitted", class: "badge-info" },
    SHORTLISTED: { label: "Shortlisted", class: "badge-success" },
    CLIENT_REVIEW: { label: "Client Review", class: "badge-warning" },
    INTERVIEW: { label: "Interview", class: "badge-accent" },
    INTERVIEWING: { label: "Interviewing", class: "badge-accent" },
    OFFER: { label: "Offer", class: "badge-success" },
    OFFERED: { label: "Offered", class: "badge-success" },
    PLACED: { label: "Placed", class: "badge-success" },
    REJECTED: { label: "Rejected", class: "badge-danger" },
    WITHDRAWN: { label: "Withdrawn", class: "badge-muted" },
    NEW: { label: "New", class: "badge-info" },
    SCREENING: { label: "Screening", class: "badge-warning" },
    READY: { label: "Ready", class: "badge-success" },
    ON_HOLD: { label: "On Hold", class: "badge-warning" },
    INACTIVE: { label: "Inactive", class: "badge-muted" },
    EXPECTED: { label: "Expected", class: "badge-warning" },
    CONFIRMED: { label: "Confirmed", class: "badge-success" },
    JOINED: { label: "Joined", class: "badge-success" },
    DID_NOT_JOIN: { label: "Did Not Join", class: "badge-danger" },
    CANCELLED: { label: "Cancelled", class: "badge-muted" }
  };

  const item = map[status] || { label: status, class: "badge-muted" };
  return `<span class="badge-status ${item.class}">${item.label}</span>`;
}

/* ================================================================
   CRM SIDE DRAWER
   ================================================================ */
export function openDrawer(title, htmlContent) {
  const existingDrawer = document.getElementById("drawer-overlay");
  if (existingDrawer) existingDrawer.remove();

  const drawerOverlay = document.createElement("div");
  drawerOverlay.id = "drawer-overlay";
  drawerOverlay.className = "drawer-overlay";
  document.body.appendChild(drawerOverlay);

  drawerOverlay.innerHTML = `
    <div class="drawer-card">
      <div class="drawer-header">
        <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); margin: 0;">${title}</h3>
        <button class="drawer-close btn-icon" aria-label="Close Drawer" style="border: none; font-size: 1.25rem; cursor: pointer;">&times;</button>
      </div>
      <div class="drawer-body">
        ${htmlContent}
      </div>
    </div>
  `;

  drawerOverlay.style.display = "flex";
  requestAnimationFrame(() => {
    drawerOverlay.classList.add("active");
  });

  const closeDrawer = () => {
    drawerOverlay.classList.remove("active");
    setTimeout(() => {
      drawerOverlay.remove();
    }, 250);
  };

  const closeBtn = drawerOverlay.querySelector(".drawer-close");
  if (closeBtn) closeBtn.addEventListener("click", closeDrawer);

  drawerOverlay.addEventListener("click", (e) => {
    if (e.target === drawerOverlay) closeDrawer();
  });

  const escHandler = (e) => {
    if (e.key === "Escape") {
      closeDrawer();
      document.removeEventListener("keydown", escHandler);
    }
  };
  document.addEventListener("keydown", escHandler);

  return { closeDrawer, drawerOverlay };
}

/* ================================================================
   RELATIVE TIME FORMATTER
   ================================================================ */
export function formatRelativeTime(dateString) {
  if (!dateString) return "Never";
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.round(diffMs / 60000);
  const diffHours = Math.round(diffMs / 3600000);
  const diffDays = Math.round(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}

/* ================================================================
   PASSWORD VISIBILITY TOGGLE
   ================================================================ */
export function initPasswordToggle(container = document) {
  const root = container || document;
  const passwordInputs = root.querySelectorAll('input[type="password"], input[data-password-toggle="true"]');

  passwordInputs.forEach((input) => {
    if (input.dataset.toggleInitialized === "true") return;
    input.dataset.toggleInitialized = "true";
    input.setAttribute("data-password-toggle", "true");

    const parent = input.parentElement;
    if (parent && !parent.classList.contains("password-toggle-wrapper")) {
      parent.classList.add("password-toggle-wrapper");
    }

    input.style.paddingRight = "2.5rem";

    const toggleBtn = document.createElement("button");
    toggleBtn.type = "button";
    toggleBtn.className = "password-toggle-btn";
    toggleBtn.setAttribute("aria-label", "Show password");
    toggleBtn.title = "Show password";
    toggleBtn.tabIndex = 0;
    toggleBtn.innerHTML = getIcon("eye", "", 16);

    toggleBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();

      const isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";

      toggleBtn.innerHTML = isPassword ? getIcon("eye-off", "", 16) : getIcon("eye", "", 16);
      const label = isPassword ? "Hide password" : "Show password";
      toggleBtn.setAttribute("aria-label", label);
      toggleBtn.title = label;
      toggleBtn.style.color = isPassword ? "var(--primary-color)" : "var(--text-muted)";
    });

    if (parent) {
      parent.appendChild(toggleBtn);
    }
  });
}

/* ================================================================
   PASSWORD STRENGTH EVALUATOR & LIVE METER
   ================================================================ */
export function evaluatePasswordStrength(password) {
  const pwd = password || "";
  const requirements = {
    length: pwd.length >= 8,
    uppercase: /[A-Z]/.test(pwd),
    lowercase: /[a-z]/.test(pwd),
    number: /[0-9]/.test(pwd),
    special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pwd)
  };

  let validCount = Object.values(requirements).filter(Boolean).length;
  if (pwd.length === 0) validCount = 0;

  let label = "Very Weak";
  let color = "var(--danger-color)";
  let percent = 10;

  if (validCount >= 5 && pwd.length >= 10) {
    label = "Strong";
    color = "var(--success-color)";
    percent = 100;
  } else if (validCount >= 4) {
    label = "Good";
    color = "var(--accent-color)";
    percent = 80;
  } else if (validCount >= 3) {
    label = "Fair";
    color = "var(--warning-color)";
    percent = 60;
  } else if (validCount >= 2) {
    label = "Weak";
    color = "var(--danger-color)";
    percent = 35;
  } else {
    label = "Very Weak";
    color = "var(--danger-color)";
    percent = 15;
  }

  return { validCount, label, color, percent, requirements };
}

export function initPasswordStrengthIndicator(inputEl, containerEl) {
  if (!inputEl || !containerEl) return;

  const updateView = () => {
    const pwd = inputEl.value || "";
    if (!pwd) {
      containerEl.style.display = "none";
      return;
    }
    containerEl.style.display = "block";

    const { label, color, percent, requirements } = evaluatePasswordStrength(pwd);

    const renderReq = (met, text) => `
      <div style="display: flex; align-items: center; gap: 0.35rem; color: ${met ? 'var(--success-color)' : 'var(--text-muted)'};">
        ${getIcon(met ? "check" : "close", "", 12)}
        <span>${text}</span>
      </div>
    `;

    containerEl.innerHTML = `
      <div style="margin-top: 0.5rem; font-size: 0.775rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
          <span style="color: var(--text-secondary);">Strength:</span>
          <strong style="color: ${color};">${label}</strong>
        </div>
        <div style="height: 5px; background: var(--border-color); border-radius: 3px; overflow: hidden; margin-bottom: 0.6rem;">
          <div style="width: ${percent}%; height: 100%; background: ${color}; transition: width 200ms ease, background 200ms ease;"></div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.25rem 0.5rem; font-size: 0.725rem;">
          ${renderReq(requirements.length, "At least 8 characters")}
          ${renderReq(requirements.uppercase, "Uppercase letter")}
          ${renderReq(requirements.lowercase, "Lowercase letter")}
          ${renderReq(requirements.number, "Number")}
          ${renderReq(requirements.special, "Special character")}
        </div>
      </div>
    `;
  };

  inputEl.addEventListener("input", updateView);
  inputEl.addEventListener("focus", updateView);
}

/* ================================================================
   FIELD VALIDATION UTILITIES
   ================================================================ */
export function validateFullName(name) {
  if (!name || typeof name !== "string") return false;
  const trimmed = name.trim();
  if (trimmed.length < 2 || trimmed.length > 80) return false;
  // Reject digits, emails, URLs, or garbage characters
  if (/[0-9]/.test(trimmed) || /@/.test(trimmed) || /https?:\/\//i.test(trimmed)) return false;
  // Allow Unicode letters, spaces, hyphens, and apostrophes
  return /^[\p{L}\s'-]+$/u.test(trimmed);
}

export function validateEmail(email) {
  if (!email || typeof email !== "string") return false;
  const clean = email.trim().toLowerCase();
  // Support demo account
  if (clean === "demo@nxtmov.local") return true;
  // Standard RFC regex
  return /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(clean);
}

export function validatePhone(phone) {
  if (!phone || typeof phone !== "string") return false;
  const clean = phone.trim();
  const digits = clean.replace(/\D/g, "");
  return digits.length >= 7 && digits.length <= 16;
}

export function validateUrl(url) {
  if (!url || typeof url !== "string") return false;
  const trimmed = url.trim();
  try {
    const parsed = new URL(trimmed.startsWith("http") ? trimmed : `https://${trimmed}`);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

export function validateLinkedinUrl(url) {
  if (!url || typeof url !== "string") return false;
  const trimmed = url.trim();
  return /^(https?:\/\/)?(www\.)?linkedin\.com\/(in|company)\/[a-zA-Z0-9_-]+\/?$/i.test(trimmed);
}

export function validateGithubUrl(url) {
  if (!url || typeof url !== "string") return false;
  const trimmed = url.trim();
  return /^(https?:\/\/)?(www\.)?github\.com\/[a-zA-Z0-9_-]+\/?$/i.test(trimmed);
}

export function validateYear(year) {
  if (year === null || year === undefined || year === "") return true;
  const y = parseInt(year, 10);
  return !isNaN(y) && y >= 1970 && y <= 2035;
}

export function validateSalary(salary) {
  if (salary === null || salary === undefined || salary === "") return true;
  const s = parseFloat(salary);
  return !isNaN(s) && s >= 0 && s <= 100000000;
}

export function validateNoticePeriod(days) {
  if (days === null || days === undefined || days === "") return true;
  const d = parseInt(days, 10);
  return !isNaN(d) && d >= 0 && d <= 365;
}
