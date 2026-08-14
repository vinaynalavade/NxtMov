# NxtMov v1.0.0 — Release Candidate Notes

**Release Date:** August 12, 2026  
**Version:** v1.0.0 (Release Candidate)  
**Product:** NxtMov — Unified Job & Recruitment Management Platform  

---

## 🚀 Overview

NxtMov v1.0.0 is the baseline release of the unified Job & Recruitment Management Platform. Designed for both individual job seekers managing their personal career search and recruitment consultancies managing agency candidate pipelines, NxtMov delivers clear actionability through its core philosophy: **"Always make the user's next move obvious."**

---

## 🌟 Key Features in v1.0.0

### 1. Individual Job Search Workflow (Core Priority)
- **Personal Workspace Auto-Provisioning**: Every registered user automatically receives an isolated personal workspace (`OrgType.INDIVIDUAL`).
- **Employer & HR Contacts CRM**: Manage client companies, HR contacts, designations, phone numbers, and communication history.
- **Call Logging & Auto-Follow-ups**: Record call types, outcomes (`Opportunity Available`, `Resume Requested`, `Not Relevant`), duration, and notes. Auto-creates "Next Move" follow-up action items.
- **Next Move Action Engine**: Dashboard KPI board and task view categorizing action items into `Today`, `Overdue`, `Upcoming`, and `Completed`.
- **Job Opportunities & Application Tracking**: Track job openings, required skills, employment types, work modes (`REMOTE`, `HYBRID`, `ONSITE`), salary ranges, application pipeline stages (`APPLIED`, `SCREENING`, `INTERVIEWING`, `OFFERED`, `REJECTED`), and interview rounds.

### 2. Preserved Advanced Consultancy Capabilities (Frozen for v1.0.0)
- **Consultancy Organizations & Context Switching**: Create agency organizations (`OrgType.CONSULTANCY`) and switch seamlessly between personal and consultancy contexts without data leakage.
- **Team Management & Role-Based Access Control (RBAC)**: Manage team members and email invitations across roles (`ADMIN`, `RECRUITER`, `COUNSELOR`, `CANDIDATE`).
- **Managed Candidate Database**: Track candidate profiles, total experience, notice period, expected salary, current company, primary/secondary skills, and assigned counselors/recruiters.
- **NxtMov Candidate Matching Engine**: Deterministic algorithm evaluating skills match (50%), experience match (25%), location & work mode match (15%), and salary budget match (10%), generating a transparent 0-100% match score with explicit `pros` and `gaps`.
- **Submissions & Placement Pipeline**: Track candidate submissions sent to client HRs and record confirmed placements.

### 3. Spreadsheet Data Import & Duplicate Engine
- Dual-mode importer supporting both `.xlsx` and `.csv` spreadsheets for `HR_CONTACTS` and `CANDIDATES`.
- Flexible header synonym auto-mapping.
- Duplicate detection checking workspace email addresses (`EXACT_DUPLICATE`) and normalized phone numbers (`POSSIBLE_DUPLICATE`).
- Atomic batch insertion inside database transaction blocks.

### 4. Enterprise Security & Architecture
- **SHA-256 Pre-Hashing**: Passwords pre-hashed via SHA-256 before `bcrypt` hashing, converting inputs into a fixed 32-byte digest and eliminating `bcrypt`'s 72-byte truncation limitation without losing entropy.
- **Multi-Tenant Context Isolation**: Server-enforced dependency injection (`get_current_tenant`) guarantees 100% data boundary protection.
- **Zero-Build Vanilla JS SPA**: Lightweight, responsive frontend engine supporting Desktop (1920x1080), Laptop (1366x768), Tablet (768px), and Mobile (390px).

---

## 🧪 Automated Testing Verification

Passed 100% of automated backend test suite (16/16 tests passing):
- `test_activity.py` (Call logging & follow-ups)
- `test_auth.py` (Registration, login, profile, workspace switching)
- `test_consultancy_workflow.py` (Full agency workflow: Org -> Invites -> Requirements -> Candidates -> Match Engine -> Submission -> Placement -> Importer -> Stats)
- `test_crm.py` (Company & HR Contact CRUD)
- `test_dev_seed.py` (Performance & seed data generation)
- `test_e2e_workflow.py` (Full individual job seeker end-to-end workflow)
- `test_health.py` (Health check)
- `test_import.py` (CSV import preview & confirm)
- `test_rbac_permissions.py` (RBAC & cross-workspace isolation)
- `test_security_password.py` (SHA-256 pre-hashing password security)
- `test_tenant_isolation.py` (Strict multi-tenant security isolation)

---

## 🔒 Known Limitations & Deferred Items
1. **Windows Desktop Packaging**: Web application source of truth is stabilized; Tauri/Electron desktop wrapper packaging is scheduled for the subsequent v1.0.0 desktop milestone.
2. **Email Delivery Provider**: Invitation tokens are generated and stored securely in the database; real SMTP/Sendgrid delivery integration is ready for future deployment.
