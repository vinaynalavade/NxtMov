# NxtMov Implementation Roadmap

This document outlines the phased development plan for building **NxtMov**.

---

## 🚩 Phase 0: Technical Architecture & Foundation Setup *(COMPLETED)*
- [x] Establish directory structure in `x:\NxtMov`.
- [x] Document System Architecture ([`ARCHITECTURE.md`](file:///x:/NxtMov/docs/ARCHITECTURE.md)).
- [x] Document Relational Database Model & ERD ([`DATABASE.md`](file:///x:/NxtMov/docs/DATABASE.md)).
- [x] Document Technology Decisions & Rationale ([`DECISIONS.md`](file:///x:/NxtMov/docs/DECISIONS.md)).

---

## ⚙️ Phase 1: Development Infrastructure & Backend Core *(COMPLETED)*
- [x] Initialize Python environment & dependencies (FastAPI, Uvicorn, SQLAlchemy 2.0, Alembic, Bcrypt, Pytest, OpenPyXL, SlowAPI).
- [x] Configure Alembic migration environment and unified schema setup (`alembic upgrade head`).

---

## 🔐 Phase 2: Authentication & Personal Workspace Provisioning *(COMPLETED)*
- [x] Build `/api/v1/auth/register`, `/login`, `/me`, `/switch` endpoints.
- [x] SHA-256 pre-hashing before bcrypt password hashing (eliminates byte truncation issues).
- [x] Server-enforced active tenant context dependency injectors (`get_current_tenant`).

---

## 🏢 Phase 3: Companies & HR Contacts CRM *(COMPLETED)*
- [x] Companies CRUD, search, and related HR contacts.
- [x] HR Contacts CRUD, status filters, and call activity history.

---

## 📞 Phase 4: Calls & "Next Move" Follow-ups Engine *(COMPLETED)*
- [x] Call logging with automated contact status updates.
- [x] Next Move task board with due date filters (`today`, `overdue`, `upcoming`, `completed`).

---

## 📊 Phase 5: Excel & CSV Import Engine *(COMPLETED)*
- [x] Dual-mode importer supporting both `HR_CONTACTS` and `CANDIDATES` spreadsheet uploads.
- [x] Header synonym auto-mapping and email/phone duplicate tagging (`NEW`, `EXACT_DUPLICATE`, `POSSIBLE_DUPLICATE`).
- [x] Atomic batch insertion inside database transaction blocks.

---

## 🎯 Phase 6: Job Opportunities & Requisitions *(COMPLETED)*
- [x] Job requirements board (`/api/v1/requirements`) with skills, salary ranges, employment types, work modes (`REMOTE`, `HYBRID`, `ONSITE`), and priorities.

---

## 📑 Phase 7: Individual Applications & Interview Tracker *(COMPLETED)*
- [x] Personal application stage pipeline (`APPLIED`, `SCREENING`, `INTERVIEWING`, `OFFERED`, `REJECTED`).
- [x] Interview scheduling and outcome tracking.

---

## 🏢 Phase 8: Consultancy Workspace & Team Management *(COMPLETED)*
- [x] Consultancy Organization creation (`type='CONSULTANCY'`).
- [x] Workspace Switcher (`/auth/switch`) toggling seamlessly between `INDIVIDUAL` and `CONSULTANCY` contexts.
- [x] Organization Team Invitations & RBAC (`ADMIN`, `RECRUITER`, `COUNSELOR`, `CANDIDATE`).

---

## 🎓 Phase 9: Managed Candidate Database & Profile 360 *(COMPLETED)*
- [x] Managed candidate database (`/api/v1/candidates`) with experience, notice period, expected salary, current company, primary/secondary skills, and assigned counselors/recruiters.
- [x] Candidate Profile 360 view with application, submission, and document attachments (`RESUME`, `CERTIFICATE`, `ID_DOCUMENT`).

---

## 🎯 Phase 10: Deterministic Candidate Matching Engine *(COMPLETED)*
- [x] NxtMov Match Score algorithm (0-100%) evaluating skills (50%), experience (25%), location & work mode (15%), and salary budget (10%).
- [x] Match explanation breakdown providing explicit match `pros` and `gaps`.
- [x] Candidate-to-requirement match APIs (`/requirements/{id}/matches` & `/candidates/{id}/matches`).

---

## 🚀 Phase 11: Candidate Submissions & Placement Pipeline *(COMPLETED)*
- [x] Candidate Submissions tracker (`/api/v1/submissions`) linking Candidate -> Job Requirement -> Recruiter across pipeline stages (`SUBMITTED`, `SHORTLISTED`, `CLIENT_REVIEW`, `INTERVIEW`, `OFFER`, `PLACED`).
- [x] Placement tracking (`/api/v1/placements`) recording confirmed placements, join dates, offered salaries, and billing amounts.

---

## 🔒 Phase 12: Security & Multi-Tenant Verification *(COMPLETED)*
- [x] Comprehensive test suites ([`test_consultancy_workflow.py`](file:///x:/NxtMov/backend/tests/test_consultancy_workflow.py), [`test_rbac_permissions.py`](file:///x:/NxtMov/backend/tests/test_rbac_permissions.py), [`test_security_password.py`](file:///x:/NxtMov/backend/tests/test_security_password.py)).
- [x] Verified 100% passing rate across all 15 automated test modules.
