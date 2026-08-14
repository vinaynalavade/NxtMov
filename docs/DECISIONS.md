# NxtMov — Architecture & Engineering Decisions (ADR)

This document records the architectural decisions, design rationale, and engineering trade-offs made during the development of **NxtMov**.

---

## 1. Password Security Hashing Strategy: SHA-256 Pre-Hashing before Bcrypt
- **Context**: `bcrypt` standard library implementations limit input passwords to a maximum of 72 bytes. Silent length truncation creates security vulnerabilities where `Password123` and `Password123` + 100 extra characters become equivalent.
- **Decision**: Pre-hash all user input passwords using SHA-256 (`hashlib.sha256(password.encode('utf-8')).hexdigest()`) before passing to `bcrypt.hashpw` and `bcrypt.checkpw`.
- **Rationale**: SHA-256 produces a fixed 32-byte digest string for any password length (from 1 character to 10,000+ characters), which is well under `bcrypt`'s 72-byte limit. This preserves 100% entropy, prevents truncation collisions, and eliminates `passlib` compatibility issues under modern Python runtimes.

---

## 2. Multi-Tenant Server-Enforced Context Injection
- **Context**: NxtMov must support isolated personal workspaces (`OrgType.INDIVIDUAL`) and consultancy organizations (`OrgType.CONSULTANCY`) on the same codebase.
- **Decision**: Embed `active_org_id` and `role` in JWT token claims. Enforce server-side context extraction via FastAPI dependency injector (`get_current_tenant`).
- **Rationale**: Guarantees that every database query automatically filters by `organization_id == ctx.organization.id`. Prevents cross-tenant data leaks and prevents organization admins from accessing private personal workspace records.

---

## 3. Database Schema Naming Conventions & Alembic Batch Migrations
- **Context**: SQLite does not support native `ALTER TABLE ALTER COLUMN TYPE` or `DROP CONSTRAINT` without temporary table migration blocks.
- **Decision**: Configure explicit `naming_convention` dictionary on SQLAlchemy `DeclarativeBase.metadata` and enable `render_as_batch=True` in `alembic/env.py`.
- **Rationale**: Autogenerates explicit constraint names (e.g. `fk_candidates_assigned_recruiter_users`) and allows Alembic to handle SQLite table alterations safely via batch copy blocks.

---

## 4. Deterministic Candidate Matching Algorithm ("NxtMov Match Score")
- **Context**: Recruitment consultancies need transparent candidate matching without opaque black-box AI scores.
- **Decision**: Implement a deterministic weighted scoring engine ([`backend/app/services/matching_service.py`](file:///x:/NxtMov/backend/app/services/matching_service.py)):
  - **Skills Match** (50% Weight): Intersection of candidate skills vs required skills.
  - **Experience Match** (25% Weight): Candidate experience vs requirement experience range.
  - **Location & Work Mode Match** (15% Weight): Remote or city location matching.
  - **Salary Budget Match** (10% Weight): Expected salary vs requirement maximum budget.
- **Rationale**: Generates an actionable 0-100% score accompanied by explicit `pros` (e.g. `✓ Possesses required skill: FastAPI`) and `gaps` (e.g. `⚠ Missing skill: Kubernetes`).

---

## 5. Zero-Build Modular Vanilla JS Single Page Application (SPA)
- **Context**: The frontend needs fast page loads, dark/light styling, modal overlays, and zero build tool overhead.
- **Decision**: Use ES Modules (`import/export`), Native Fetch API client (`js/api.js`), Pub-Sub State Store (`js/store.js`), and Hash Router (`js/router.js`).
- **Rationale**: Allows instant execution without Node.js build steps, Webpack, or Babel overhead, making local development and future Tauri/Electron desktop wrapping simple.

---

## 6. v1.0.0 Feature Freeze & Web Release Candidate Strategy
- **Context**: NxtMov has accumulated extensive functionality across individual job search and agency consultancy workflows.
- **Decision**: Freeze feature development at v1.0.0 Release Candidate. Focus exclusively on stabilization, audit, testing, responsive polish, and documentation.
- **Rationale**: Establishes a rock-solid, 100% tested web baseline before proceeding to Windows desktop app packaging.
