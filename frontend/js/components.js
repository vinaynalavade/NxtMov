import { normalizeErrorMessage } from "./api.js";

/* ================================================================
   TOAST NOTIFICATIONS — Single source of truth
   ================================================================ */
const MAX_TOASTS = 5;
const TOAST_DURATION = 4000;

export function showToast(message, type = "success") {
  const cleanMessage = normalizeErrorMessage(message);

  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  // Prevent duplicate toasts with same message
  const existing = container.querySelectorAll(".toast");
  for (const t of existing) {
    if (t.dataset.msg === cleanMessage) return;
  }

  // Cap max visible toasts
  while (container.children.length >= MAX_TOASTS) {
    container.firstChild.remove();
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.dataset.msg = cleanMessage;
  toast.innerHTML = `
    <span>${cleanMessage}</span>
    <button class="toast-close" aria-label="Dismiss">&times;</button>
  `;

  toast.querySelector(".toast-close").addEventListener("click", () => removeToast(toast));
  container.appendChild(toast);

  setTimeout(() => removeToast(toast), TOAST_DURATION);
}

function removeToast(toast) {
  if (!toast || !toast.parentNode) return;
  toast.style.opacity = "0";
  toast.style.transform = "translateY(8px)";
  setTimeout(() => toast.remove(), 150);
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
        <h3>${title}</h3>
        <button class="modal-close" aria-label="Close">&times;</button>
      </div>
      <div class="modal-body">
        ${htmlContent}
      </div>
    </div>
  `;

  modalOverlay.style.display = "flex";

  const closeModal = () => {
    modalOverlay.style.display = "none";
    // Cleanup after animation
    setTimeout(() => modalOverlay.remove(), 100);
  };

  // Close on X button
  const closeBtn = modalOverlay.querySelector(".modal-close");
  if (closeBtn) closeBtn.addEventListener("click", closeModal);

  // Close on any .close-modal-btn
  modalOverlay.querySelectorAll(".close-modal-btn").forEach((btn) => {
    btn.addEventListener("click", closeModal);
  });

  // Close on overlay backdrop click
  modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) closeModal();
  });

  // Close on Escape key
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
  // Clean up any existing drawer
  const existingDrawer = document.getElementById("drawer-overlay");
  if (existingDrawer) existingDrawer.remove();

  const drawerOverlay = document.createElement("div");
  drawerOverlay.id = "drawer-overlay";
  drawerOverlay.className = "drawer-overlay";
  document.body.appendChild(drawerOverlay);

  drawerOverlay.innerHTML = `
    <div class="drawer-card">
      <div class="drawer-header">
        <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary);">${title}</h3>
        <button class="drawer-close btn-icon" aria-label="Close Drawer" style="border: none; font-size: 1.25rem;">&times;</button>
      </div>
      <div class="drawer-body">
        ${htmlContent}
      </div>
    </div>
  `;

  // Show with animation (next frame to trigger CSS transition)
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

  // Close on Escape key
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
    toggleBtn.innerHTML = "👁️";

    toggleBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();

      const isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";

      toggleBtn.innerHTML = isPassword ? "🙈" : "👁️";
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
