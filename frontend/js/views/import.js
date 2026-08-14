import { api } from "../api.js";
import { showToast, formatBadge } from "../components.js";

export function renderImport() {
  return `
    <div class="view-header">
      <div>
        <h1 class="view-title">📊 Spreadsheet Onboarding & Import Engine</h1>
        <p class="view-subtitle">Intelligently clean, map, normalize, and ingest HR contacts or talent databases into NxtMov CRM.</p>
      </div>
    </div>

    <!-- Step 1: Import Configuration & Upload Area -->
    <div id="import-step-upload" class="card" style="margin-bottom: 2rem;">
      <!-- Dynamic Error Banner Container -->
      <div id="import-error-banner" style="display: none; background-color: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger-color); border-radius: var(--radius-lg); padding: 1.25rem; margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
          <div style="font-size: 1.5rem; color: var(--danger-color);">⚠️</div>
          <div style="flex: 1;">
            <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--danger-color); margin-bottom: 0.25rem;">Unable to process spreadsheet</h4>
            <p id="import-error-message" style="font-size: 0.85rem; color: var(--text-primary); margin-bottom: 0.75rem;">-</p>
            <div style="display: flex; gap: 0.5rem;">
              <button id="error-retry-btn" class="btn btn-outline" style="font-size: 0.775rem; padding: 0.35rem 0.75rem;">🔄 Try Again</button>
              <button id="error-reselect-btn" class="btn btn-primary" style="font-size: 0.775rem; padding: 0.35rem 0.75rem;">📄 Browse Another File</button>
            </div>
          </div>
        </div>
      </div>

      <div style="margin-bottom: 1.5rem;">
        <label style="font-weight: 700; font-size: 0.95rem; display: block; margin-bottom: 0.75rem;">1. Select Data Type</label>
        <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
          <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; font-size: 0.9rem; font-weight: 500;">
            <input type="radio" name="import_type_radio" value="HR_CONTACTS" checked />
            🏢 HR / Recruiter Contacts & Employer Companies
          </label>
          <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; font-size: 0.9rem; font-weight: 500;">
            <input type="radio" name="import_type_radio" value="CANDIDATES" />
            🎓 Candidates / Talent Database
          </label>
        </div>
      </div>

      <!-- Drag & Drop Area -->
      <div id="drop-zone" style="border: 2px dashed var(--border-hover); border-radius: var(--radius-xl); padding: 3rem 1.5rem; text-align: center; background-color: var(--bg-secondary); transition: all var(--transition-fast); cursor: pointer;">
        <div style="font-size: 3rem; margin-bottom: 0.75rem;">📄</div>
        <h3 style="font-size: 1.15rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.35rem;">Drag & drop your Excel or CSV file here</h3>
        <p style="color: var(--text-muted); font-size: 0.85rem; max-width: 480px; margin: 0 auto 1.25rem auto;">
          Supports <strong>.xlsx</strong> and <strong>.csv</strong>. NxtMov automatically detects column headers, synonym variations, and duplicate records.
        </p>

        <input type="file" id="import-file-input" accept=".xlsx, .csv" style="display: none;">
        <button id="select-file-btn" type="button" class="btn btn-primary btn-lg">Browse Spreadsheet File</button>
      </div>

      <!-- Selected File Card (Hidden by default) -->
      <div id="file-info-card" style="display: none; background-color: var(--bg-primary); border: 1px solid var(--border-color); border-radius: var(--radius-lg); padding: 1.25rem; margin-top: 1.25rem; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 1rem;">
          <div style="font-size: 2rem;">📊</div>
          <div>
            <div id="file-info-name" style="font-weight: 700; font-size: 0.95rem;">-</div>
            <div id="file-info-size" style="font-size: 0.775rem; color: var(--text-muted);">-</div>
          </div>
        </div>
        <div style="display: flex; gap: 0.75rem;">
          <button id="replace-file-btn" class="btn btn-outline" style="font-size: 0.8rem;">✖ Replace File</button>
          <button id="analyze-file-btn" class="btn btn-primary" style="font-size: 0.85rem;">🔍 Analyze & Map File</button>
        </div>
      </div>
    </div>

    <!-- Step 2: Mapping & Preview Container (Initially Hidden) -->
    <div id="import-step-preview" class="card" style="display: none;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-color); padding-bottom: 1rem; flex-wrap: wrap; gap: 1rem;">
        <div>
          <h3 id="preview-filename" style="font-size: 1.15rem; font-weight: 700; color: var(--text-primary);">Import Preview</h3>
          <p id="preview-stats-summary" style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;"></p>
        </div>
        <div style="display: flex; gap: 0.75rem; align-items: center;">
          <!-- Sheet Selector -->
          <div id="sheet-selector-wrapper" style="display: none; align-items: center; gap: 0.5rem;">
            <label style="font-size: 0.8rem; font-weight: 600;">Sheet:</label>
            <select id="sheet-select" class="form-input" style="padding: 0.35rem 0.6rem; font-size: 0.8rem; width: auto;"></select>
          </div>

          <button id="cancel-import-btn" class="btn btn-outline">Cancel</button>
          <button id="confirm-import-btn" class="btn btn-primary">Confirm & Import Records</button>
        </div>
      </div>

      <!-- Column Mapping Controls -->
      <div style="margin-bottom: 2rem; background-color: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-lg); padding: 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <div>
            <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary);">1. Smart Column Mapping</h4>
            <p style="font-size: 0.775rem; color: var(--text-muted);">Review detected column headers and correct any unmapped or ambiguous fields.</p>
          </div>
        </div>

        <div id="column-mapping-container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem;">
          <!-- Dynamic Mappings -->
        </div>
      </div>

      <!-- Duplicate Handling Policy Selector -->
      <div style="margin-bottom: 2rem; background-color: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-lg); padding: 1.25rem;">
        <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.75rem;">2. Duplicate Handling Policy</h4>
        <div style="display: flex; gap: 1.5rem; flex-wrap: wrap;">
          <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; font-size: 0.875rem;">
            <input type="radio" name="duplicate_policy_radio" value="SKIP" checked />
            <strong>Skip Duplicates</strong> (Safest: do not import duplicate email/phone)
          </label>
          <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; font-size: 0.875rem;">
            <input type="radio" name="duplicate_policy_radio" value="UPDATE" />
            <strong>Update Existing Records</strong> (Merge & update fields)
          </label>
          <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; font-size: 0.875rem;">
            <input type="radio" name="duplicate_policy_radio" value="IMPORT_ALL" />
            <strong>Import All Records</strong> (Create duplicate entries)
          </label>
        </div>
      </div>

      <!-- Preview Data Table -->
      <div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
          <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary);">3. Record Preview & Duplicate Analysis</h4>
          <span id="preview-row-count-badge" class="badge-status badge-info" style="font-size: 0.75rem;">Showing records</span>
        </div>
        
        <div id="preview-table-container">
          <!-- Dynamic Table -->
        </div>
      </div>
    </div>

    <!-- Step 3: Success Result Modal / Card (Initially Hidden) -->
    <div id="import-step-result" class="card" style="display: none; padding: 2.5rem; text-align: center;">
      <div style="font-size: 3.5rem; margin-bottom: 1rem;">🎉</div>
      <h2 id="result-title" style="font-size: 1.5rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.5rem;">Import Completed Successfully!</h2>
      <p id="result-message" style="color: var(--text-secondary); font-size: 0.95rem; max-width: 520px; margin: 0 auto 1.5rem auto;"></p>

      <div id="result-breakdown-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1rem; max-width: 600px; margin: 0 auto 2rem auto;">
        <!-- Breakdown KPIs -->
      </div>

      <div style="display: flex; gap: 1rem; justify-content: center;">
        <button id="result-import-another-btn" class="btn btn-outline">📊 Import Another File</button>
        <a id="result-go-crm-btn" href="#/contacts" class="btn btn-primary">📞 Go to HR Contacts CRM</a>
      </div>
    </div>
  `;
}

export function initImportListeners() {
  const fileInput = document.getElementById("import-file-input");
  const selectBtn = document.getElementById("select-file-btn");
  const dropZone = document.getElementById("drop-zone");
  const fileInfoCard = document.getElementById("file-info-card");
  const fileNameDisplay = document.getElementById("file-info-name");
  const fileSizeDisplay = document.getElementById("file-info-size");
  const replaceFileBtn = document.getElementById("replace-file-btn");
  const analyzeFileBtn = document.getElementById("analyze-file-btn");

  const cancelBtn = document.getElementById("cancel-import-btn");
  const confirmBtn = document.getElementById("confirm-import-btn");
  const sheetSelect = document.getElementById("sheet-select");
  const resultImportAnotherBtn = document.getElementById("result-import-another-btn");

  let selectedFile = null;
  let currentPreviewData = null;

  const errorBanner = document.getElementById("import-error-banner");
  const errorMessageEl = document.getElementById("import-error-message");
  const errorRetryBtn = document.getElementById("error-retry-btn");
  const errorReselectBtn = document.getElementById("error-reselect-btn");

  function hideImportError() {
    if (errorBanner) errorBanner.style.display = "none";
  }

  function showImportError(err) {
    if (errorBanner && errorMessageEl) {
      errorBanner.style.display = "block";
      errorMessageEl.textContent = err.message || String(err);
    }
  }

  if (errorRetryBtn) {
    errorRetryBtn.onclick = async () => {
      if (selectedFile) {
        hideImportError();
        await uploadAndPreview(selectedFile);
      }
    };
  }

  if (errorReselectBtn) {
    errorReselectBtn.onclick = () => {
      hideImportError();
      selectedFile = null;
      fileInput.value = "";
      fileInfoCard.style.display = "none";
      dropZone.style.display = "block";
    };
  }

  if (selectBtn && fileInput) {
    selectBtn.onclick = (e) => {
      e.stopPropagation();
      hideImportError();
      fileInput.click();
    };
  }

  if (dropZone) {
    dropZone.onclick = () => {
      hideImportError();
      fileInput.click();
    };
    dropZone.ondragover = (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--primary-color)";
      dropZone.style.backgroundColor = "var(--primary-light)";
    };
    dropZone.ondragleave = (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--border-hover)";
      dropZone.style.backgroundColor = "var(--bg-secondary)";
    };
    dropZone.ondrop = (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--border-hover)";
      dropZone.style.backgroundColor = "var(--bg-secondary)";
      hideImportError();
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFileSelected(e.dataTransfer.files[0]);
      }
    };
  }

  if (fileInput) {
    fileInput.onchange = (e) => {
      hideImportError();
      if (e.target.files && e.target.files.length > 0) {
        handleFileSelected(e.target.files[0]);
      }
    };
  }

  function handleFileSelected(file) {
    hideImportError();
    selectedFile = file;
    fileNameDisplay.textContent = file.name;
    const sizeKb = (file.size / 1024).toFixed(1);
    fileSizeDisplay.textContent = `${sizeKb} KB | Ready for analysis`;
    dropZone.style.display = "none";
    fileInfoCard.style.display = "flex";
  }

  if (replaceFileBtn) {
    replaceFileBtn.onclick = () => {
      hideImportError();
      selectedFile = null;
      fileInput.value = "";
      fileInfoCard.style.display = "none";
      dropZone.style.display = "block";
    };
  }

  if (analyzeFileBtn) {
    analyzeFileBtn.onclick = async () => {
      if (!selectedFile) return;
      hideImportError();
      await uploadAndPreview(selectedFile);
    };
  }

  async function uploadAndPreview(file, targetSheet = null) {
    const import_type = document.querySelector('input[name="import_type_radio"]:checked')?.value || "HR_CONTACTS";
    const formData = new FormData();
    formData.append("file", file);

    let url = `/import/preview?import_type=${import_type}`;
    if (targetSheet) url += `&sheet_name=${encodeURIComponent(targetSheet)}`;

    if (analyzeFileBtn) {
      analyzeFileBtn.disabled = true;
      analyzeFileBtn.textContent = "⏳ Parsing & Analyzing...";
    }

    try {
      showToast("Parsing spreadsheet headers, detecting sheets & analyzing duplicates...", "info");
      const data = await api.post(url, formData, false);
      currentPreviewData = data;
      renderPreviewStep(data);
    } catch (err) {
      showImportError(err);
      showToast(err, "danger");
    } finally {
      if (analyzeFileBtn) {
        analyzeFileBtn.disabled = false;
        analyzeFileBtn.textContent = "🔍 Analyze & Map File";
      }
    }
  }

  if (sheetSelect) {
    sheetSelect.onchange = () => {
      if (selectedFile && sheetSelect.value) {
        uploadAndPreview(selectedFile, sheetSelect.value);
      }
    };
  }

  if (cancelBtn) {
    cancelBtn.onclick = () => {
      hideImportError();
      document.getElementById("import-step-preview").style.display = "none";
      document.getElementById("import-step-upload").style.display = "block";
      selectedFile = null;
      fileInput.value = "";
      fileInfoCard.style.display = "none";
      dropZone.style.display = "block";
    };
  }

  if (confirmBtn) {
    confirmBtn.onclick = async () => {
      if (!currentPreviewData) return;

      const mapping = {};
      document.querySelectorAll(".mapping-select").forEach(sel => {
        const header = sel.getAttribute("data-header");
        mapping[header] = sel.value;
      });

      const duplicate_policy = document.querySelector('input[name="duplicate_policy_radio"]:checked')?.value || "SKIP";

      try {
        confirmBtn.disabled = true;
        confirmBtn.textContent = "⏳ Importing Records...";
        showToast("Executing batch import inside safe atomic transaction...", "info");
        const res = await api.post("/import/confirm", {
          file_token: currentPreviewData.file_name,
          import_type: currentPreviewData.import_type,
          sheet_name: currentPreviewData.selected_sheet || "Sheet1",
          mapping,
          duplicate_handling: duplicate_policy
        });

        showResultStep(res, currentPreviewData.import_type);
      } catch (err) {
        showToast(err, "danger");
      } finally {
        confirmBtn.disabled = false;
        confirmBtn.textContent = "Confirm & Import Records";
      }
    };
  }

  if (resultImportAnotherBtn) {
    resultImportAnotherBtn.onclick = () => {
      hideImportError();
      document.getElementById("import-step-result").style.display = "none";
      document.getElementById("import-step-upload").style.display = "block";
      selectedFile = null;
      fileInput.value = "";
      fileInfoCard.style.display = "none";
      dropZone.style.display = "block";
    };
  }
}

function renderPreviewStep(data) {
  document.getElementById("import-step-upload").style.display = "none";
  const previewCard = document.getElementById("import-step-preview");
  previewCard.style.display = "block";

  document.getElementById("preview-filename").textContent = `Spreadsheet Analysis: ${data.original_filename} (${data.import_type})`;
  document.getElementById("preview-stats-summary").textContent = 
    `Total Rows: ${data.total_rows} | New: ${data.summary_stats.new_count} | Exact Duplicates: ${data.summary_stats.exact_duplicates} | Possible Duplicates: ${data.summary_stats.possible_duplicates} | Invalid: ${data.summary_stats.invalid_count}`;

  // Multi-sheet selector
  const sheetWrapper = document.getElementById("sheet-selector-wrapper");
  const sheetSelect = document.getElementById("sheet-select");
  if (data.sheets && data.sheets.length > 1) {
    sheetWrapper.style.display = "flex";
    sheetSelect.innerHTML = data.sheets.map(s => `
      <option value="${s}" ${s === data.selected_sheet ? 'selected' : ''}>${s}</option>
    `).join("");
  } else {
    sheetWrapper.style.display = "none";
  }

  const isCandidate = data.import_type === "CANDIDATES";

  // Render Mapping Cards with Confidence Indicators
  const mappingContainer = document.getElementById("column-mapping-container");
  mappingContainer.innerHTML = data.column_mappings.map(col => {
    const header = col.source_header;
    const suggested = col.target_field || "ignore";
    const confidence = col.confidence;

    let confBadge = `<span class="badge-status badge-success" style="font-size: 0.65rem;">Auto-mapped</span>`;
    if (confidence === "AMBIGUOUS") {
      confBadge = `<span class="badge-status badge-warning" style="font-size: 0.65rem;">⚠️ AMBIGUOUS — VERIFY</span>`;
    } else if (confidence === "UNMAPPED") {
      confBadge = `<span class="badge-status badge-muted" style="font-size: 0.65rem;">Unmapped</span>`;
    }

    return `
      <div style="background-color: var(--bg-card); border: 1px solid ${confidence === 'AMBIGUOUS' ? 'var(--warning-color)' : 'var(--border-color)'}; padding: 0.875rem; border-radius: var(--radius-md);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
          <label style="font-size: 0.8rem; font-weight: 700; color: var(--text-primary);">Header: "${header}"</label>
          ${confBadge}
        </div>

        <select class="form-control mapping-select" data-header="${header}" style="width: 100%; font-size: 0.85rem;">
          ${isCandidate ? `
            <option value="name" ${suggested === 'name' ? 'selected' : ''}>Candidate Name</option>
            <option value="email" ${suggested === 'email' ? 'selected' : ''}>Email Address</option>
            <option value="phone" ${suggested === 'phone' ? 'selected' : ''}>Phone Number</option>
            <option value="primary_skills" ${suggested === 'primary_skills' ? 'selected' : ''}>Primary Skills</option>
            <option value="experience_years" ${suggested === 'experience_years' ? 'selected' : ''}>Experience (Years)</option>
            <option value="location" ${suggested === 'location' ? 'selected' : ''}>Location</option>
            <option value="current_company" ${suggested === 'current_company' ? 'selected' : ''}>Current Company</option>
          ` : `
            <option value="name" ${suggested === 'name' ? 'selected' : ''}>HR Contact Name</option>
            <option value="company_name" ${suggested === 'company_name' ? 'selected' : ''}>Company Name</option>
            <option value="designation" ${suggested === 'designation' ? 'selected' : ''}>Designation / Role</option>
            <option value="phone" ${suggested === 'phone' ? 'selected' : ''}>Phone / Mobile Number</option>
            <option value="email" ${suggested === 'email' ? 'selected' : ''}>Email Address</option>
            <option value="location" ${suggested === 'location' ? 'selected' : ''}>Location</option>
            <option value="linkedin_url" ${suggested === 'linkedin_url' ? 'selected' : ''}>LinkedIn Profile URL</option>
            <option value="notes" ${suggested === 'notes' ? 'selected' : ''}>Notes / Remarks</option>
          `}
          <option value="ignore" ${suggested === 'ignore' ? 'selected' : ''}>— Ignore Column —</option>
        </select>
        ${col.reason ? `<div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.25rem;">${col.reason}</div>` : ''}
      </div>
    `;
  }).join("");

  // Render Preview Table
  const tableContainer = document.getElementById("preview-table-container");
  const countBadge = document.getElementById("preview-row-count-badge");
  if (countBadge) countBadge.textContent = `Total Preview Records: ${data.preview_rows.length}`;

  tableContainer.innerHTML = `
    <div class="table-responsive">
      <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.85rem;">
        <thead>
          <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-secondary);">
            <th style="padding: 0.6rem;">ROW #</th>
            <th style="padding: 0.6rem;">NAME</th>
            <th style="padding: 0.6rem;">${isCandidate ? 'SKILLS' : 'COMPANY'}</th>
            <th style="padding: 0.6rem;">CONTACT INFO</th>
            <th style="padding: 0.6rem;">DUPLICATE & VALIDATION STATUS</th>
          </tr>
        </thead>
        <tbody>
          ${data.preview_rows.map(r => `
            <tr style="border-bottom: 1px solid var(--border-color);">
              <td style="padding: 0.6rem; color: var(--text-muted);">${r.row_number}</td>
              <td style="padding: 0.6rem;">
                <div style="font-weight: 600;">${r.name || '—'}</div>
                <div style="font-size: 0.725rem; color: var(--text-muted);">${r.designation || ''}</div>
              </td>
              <td style="padding: 0.6rem;">${isCandidate ? (r.skills || '—') : (r.company_name || '—')}</td>
              <td style="padding: 0.6rem;">
                <div>${r.phone || '—'}</div>
                <div style="font-size: 0.725rem; color: var(--text-muted);">${r.email || ''}</div>
              </td>
              <td style="padding: 0.6rem;">
                ${r.status_flag === 'NEW' ? '<span class="badge-status badge-success">New Record</span>' : ''}
                ${r.status_flag === 'EXACT_DUPLICATE' ? '<span class="badge-status badge-danger">Exact Duplicate</span>' : ''}
                ${r.status_flag === 'POSSIBLE_DUPLICATE' ? '<span class="badge-status badge-warning">Possible Duplicate</span>' : ''}
                ${r.status_flag === 'INVALID' ? '<span class="badge-status badge-muted">Invalid Data</span>' : ''}
                ${r.duplicate_reason ? `<div style="font-size: 0.725rem; color: var(--text-muted); margin-top: 0.2rem;">${r.duplicate_reason}</div>` : ''}
                ${r.issue_details ? `<div style="font-size: 0.725rem; color: var(--danger-color); margin-top: 0.2rem;">${r.issue_details}</div>` : ''}
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function showResultStep(res, importType) {
  document.getElementById("import-step-preview").style.display = "none";
  const resultCard = document.getElementById("import-step-result");
  resultCard.style.display = "block";

  document.getElementById("result-title").textContent = "Import Completed Successfully!";
  document.getElementById("result-message").textContent = res.message;

  const isCandidate = importType === "CANDIDATES";
  const grid = document.getElementById("result-breakdown-grid");

  grid.innerHTML = `
    <div style="background-color: var(--bg-secondary); border: 1px solid var(--border-color); padding: 1rem; border-radius: var(--radius-md);">
      <div style="font-size: 0.75rem; color: var(--text-muted);">${isCandidate ? 'CANDIDATES CREATED' : 'HR CONTACTS CREATED'}</div>
      <div style="font-size: 1.5rem; font-weight: 700; color: var(--accent-color); margin-top: 0.25rem;">${isCandidate ? res.imported_candidates_count : res.imported_contacts_count}</div>
    </div>
    ${!isCandidate ? `
      <div style="background-color: var(--bg-secondary); border: 1px solid var(--border-color); padding: 1rem; border-radius: var(--radius-md);">
        <div style="font-size: 0.75rem; color: var(--text-muted);">COMPANIES CREATED</div>
        <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary-color); margin-top: 0.25rem;">${res.imported_companies_count}</div>
      </div>
      <div style="background-color: var(--bg-secondary); border: 1px solid var(--border-color); padding: 1rem; border-radius: var(--radius-md);">
        <div style="font-size: 0.75rem; color: var(--text-muted);">COMPANIES REUSED</div>
        <div style="font-size: 1.5rem; font-weight: 700; color: var(--info-color); margin-top: 0.25rem;">${res.reused_companies_count}</div>
      </div>
    ` : ''}
    <div style="background-color: var(--bg-secondary); border: 1px solid var(--border-color); padding: 1rem; border-radius: var(--radius-md);">
      <div style="font-size: 0.75rem; color: var(--text-muted);">SKIPPED DUPLICATES</div>
      <div style="font-size: 1.5rem; font-weight: 700; color: var(--warning-color); margin-top: 0.25rem;">${res.skipped_duplicates_count}</div>
    </div>
  `;

  const goCrmBtn = document.getElementById("result-go-crm-btn");
  if (goCrmBtn) {
    goCrmBtn.href = isCandidate ? "#/candidates" : "#/contacts";
    goCrmBtn.textContent = isCandidate ? "🎓 Go to Candidates" : "📞 Go to HR Contacts CRM";
  }
}
