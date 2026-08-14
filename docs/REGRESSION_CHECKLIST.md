# NxtMov v1.0.0 — Manual QA & Regression Testing Checklist

This checklist defines the manual regression testing protocol for validating **NxtMov v1.0.0 Release Candidate** releases across modern web browsers.

---

## 🔐 1. Authentication & Workspace Management

- [ ] **1.1 User Registration**:
  - Register a new user (`full_name`, `email`, `password`).
  - Verify JWT access token issued and saved in localStorage.
  - Verify personal workspace (`INDIVIDUAL`) auto-provisioned.
- [ ] **1.2 Duplicate Email Registration**:
  - Attempt registering with an existing email.
  - Verify friendly validation toast error displayed (`400 Bad Request`).
- [ ] **1.3 User Login**:
  - Login with valid credentials (`username`, `password`).
  - Verify redirect to `/dashboard`.
- [ ] **1.4 Incorrect Credentials**:
  - Login with invalid password.
  - Verify error message displayed (`401 Unauthorized`).
- [ ] **1.5 Workspace Switcher**:
  - Open workspace dropdown in top header.
  - Select Consultancy workspace.
  - Verify active workspace switched and token updated.
- [ ] **1.6 Create Consultancy Workspace**:
  - Click `+ Agency` button in header.
  - Enter consultancy name, phone, website, and city location.
  - Verify workspace created and auto-switched context.

---

## 🏢 2. Employer Companies & HR Contacts CRM

- [ ] **2.1 Add Employer Company**:
  - Navigate to `/companies`.
  - Click `+ Add Company`.
  - Enter name, industry, location, and website.
  - Verify company appears in table immediately.
- [ ] **2.2 Search Companies**:
  - Type query into company search bar.
  - Verify table filters dynamically.
- [ ] **2.3 Add HR Contact**:
  - Navigate to `/contacts`.
  - Click `+ Add HR Contact`.
  - Enter contact name, designation, phone, email, and select company.
  - Verify contact created and linked to company.
- [ ] **2.4 HR Contact Status Filter**:
  - Select status filter (`Not Contacted`, `Contacted`, `Interested`, `Opportunity Available`).
  - Verify contact list updates.

---

## 📞 3. Call Logging & "Next Move" Follow-ups Engine

- [ ] **3.1 Log HR Call**:
  - From HR Contact card or list, click `📞 Log Call`.
  - Select call type (`OUTBOUND`), outcome (`OPPORTUNITY_AVAILABLE`), enter duration and notes.
  - Check `Create Follow-up` box and set due date.
  - Click `Save Call Log`.
  - Verify contact status auto-updates to `OPPORTUNITY_AVAILABLE`.
  - Verify call log appears in history.
- [ ] **3.2 View Follow-up on Dashboard**:
  - Navigate to `/dashboard`.
  - Verify follow-up task appears under `Today's Next Moves`.
- [ ] **3.3 Complete Follow-up Task**:
  - Click completion checkbox or status toggle on task.
  - Verify status changes to `COMPLETED` and task moves to completed history.
- [ ] **3.4 Next Moves Board**:
  - Navigate to `/followups`.
  - Filter by `Today`, `Overdue`, `Upcoming`, `Completed`.
  - Verify tasks correctly categorized.

---

## 📊 4. Excel & CSV Import Engine

- [ ] **4.1 Upload Spreadsheet**:
  - Navigate to `/import`.
  - Select import type: `HR / Recruiter Contacts` or `Candidates / Students`.
  - Upload `.xlsx` or `.csv` file.
  - Verify preview screen loads with detected headers.
- [ ] **4.2 Column Auto-Mapping**:
  - Verify synonym mappings (e.g. `HR Name` -> `name`, `Company` -> `company_name`, `Mobile` -> `phone`, `Email` -> `email`).
- [ ] **4.3 Duplicate Detection**:
  - Verify existing emails tagged as `EXACT_DUPLICATE`.
  - Verify existing normalized phone numbers tagged as `POSSIBLE_DUPLICATE`.
  - Verify new records tagged as `NEW`.
- [ ] **4.4 Execute Import**:
  - Click `Confirm & Import Records`.
  - Verify success toast and check records in `/contacts` or `/candidates`.

---

## 🎯 5. Job Requirements & Opportunities

- [ ] **5.1 Create Opportunity**:
  - Navigate to `/opportunities`.
  - Click `+ Add Requirement`.
  - Enter title, company, required skills, employment type (`FULL_TIME`), work mode (`HYBRID`), salary range, and status (`OPEN`).
  - Verify opportunity saved.
- [ ] **5.2 Search Opportunities**:
  - Filter by search query, company, or status.

---

## 📑 6. Job Applications & Interview Tracking

- [ ] **6.1 Create Job Application**:
  - Navigate to `/applications`.
  - Select Job Requirement and set initial stage (`APPLIED`).
  - Verify application card created.
- [ ] **6.2 Update Application Stage**:
  - Change stage to `INTERVIEWING`.
  - Verify stage badge updates.
- [ ] **6.3 Schedule Interview**:
  - Click `📅 Schedule Interview`.
  - Enter round name (`Technical Round 1`), date/time, meeting link, and interviewer names.
  - Save interview and verify interview details attached to application.

---

## 🎓 7. Consultancy Workspace & Candidate Operations

- [ ] **7.1 Team Invitations**:
  - In Consultancy workspace, navigate to `/team`.
  - Click `+ Invite Team Member`.
  - Enter email and role (`RECRUITER`).
  - Verify invitation created with token.
- [ ] **7.2 Candidate Database & Profile 360**:
  - Navigate to `/candidates`.
  - Click `+ Add Candidate`.
  - Enter candidate details, experience, skills, and expected salary.
  - Open Candidate Profile 360 view.
- [ ] **7.3 NxtMov Candidate Match Engine**:
  - On candidate or job requirement card, click `🎯 Match Jobs`.
  - Verify **NxtMov Match Score** (0-100%) and match explanation (`pros` & `gaps`).
- [ ] **7.4 Candidate Submission & Placement**:
  - Click `Submit Candidate to Job`.
  - Verify submission stage pipeline (`SUBMITTED` -> `INTERVIEW` -> `OFFER` -> `PLACED`).
  - Navigate to `/submissions` and click `🏆 Record Placement`.
  - Verify placement saved and displayed under `Confirmed Consultancy Placements`.

---

## 📱 8. Responsive Design & Browser Verification

- [ ] **8.1 Viewport Verification**:
  - Desktop (1920 × 1080)
  - Laptop (1366 × 768)
  - Tablet (768px width)
  - Mobile (390px width)
- [ ] **8.2 Verification Points**:
  - Verify table touch-scroll (`.table-responsive`).
  - Verify no horizontal body overflow.
  - Verify modal width on small screens (`width: 95%`).
  - Verify navigation bar collapse on mobile.
