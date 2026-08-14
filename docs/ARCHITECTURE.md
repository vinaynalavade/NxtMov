# NxtMov Architecture Specification

**Product Version:** 1.0.0 (Phase 0 Foundation)  
**Author:** Lead Software Architect  
**Status:** Architectural Blueprint  

---

## 1. Architectural Overview

NxtMov is designed as an **API-first, multi-tenant Job and Recruitment Management Platform** serving individual job seekers and recruitment consultancies.

### High-Level System Architecture

```text
+-----------------------------------------------------------------------+
|                             CLIENT LAYER                              |
|   Vanilla JS (ES Modules) SPA / Custom CSS / HTML5 Responsive Web     |
+-----------------------------------------------------------------------+
                                   |
                                   | HTTP REST (JSON / JWT)
                                   v
+-----------------------------------------------------------------------+
|                            FASTAPI BACKEND                            |
|                                                                       |
|  +-------------------+  +-------------------+  +-------------------+  |
|  |  Auth & JWT Sec.  |  | Tenant Isolation  |  |  CORS / Security  |  |
|  |    Middleware     |  |    Context Di     |  |    Middleware     |  |
|  +-------------------+  +-------------------+  +-------------------+  |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  |                         API ROUTERS (v1)                        |  |
|  |  /auth  /organizations  /companies  /contacts  /candidates      |  |
|  |  /requirements  /calls  /followups  /applications  /interviews  |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  |                         SERVICE LAYER                           |  |
|  |  Tenant Context Validation | Business Logic | Audit Logging     |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  |                    DATA ACCESS LAYER (SQLAlchemy)               |  |
|  |  Session Management | Tenant Scoped Query Filters | Migrations  |  |
|  +-----------------------------------------------------------------+  |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                            DATABASE LAYER                             |
|          Development: SQLite (WAL)  |  Production: PostgreSQL         |
+-----------------------------------------------------------------------+
```

---

## 2. Project Directory Structure

```text
NxtMov/
├── .gitignore
├── README.md
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── backend/
│   ├── alembic/                  # Database migration scripts
│   │   ├── versions/
│   │   └── env.py
│   ├── alembic.ini
│   ├── requirements.txt          # Python dependencies
│   ├── app/
│   │   ├── main.py               # FastAPI application entry point
│   │   ├── api/                  # API routes & endpoints
│   │   │   └── v1/
│   │   │       ├── api.py        # Central v1 router aggregation
│   │   │       └── endpoints/    # Feature-specific router endpoints
│   │   ├── core/                 # Core configs, auth, security & DB session
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   └── tenant.py         # Tenant isolation context manager
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic schemas (Request/Response)
│   │   ├── crud/                 # Data access queries & operations
│   │   └── services/             # Domain business logic
│   └── tests/                    # Pytest suite (Unit, Integration, RBAC)
├── frontend/
│   ├── index.html                # Single Application Shell
│   ├── css/
│   │   ├── main.css              # Reset & layout styles
│   │   ├── variables.css         # Design tokens & color variables
│   │   └── components.css        # Card, modal, table, badge styles
│   └── js/
│       ├── app.js                # App bootstrap & routing initializer
│       ├── router.js             # Client-side hash/history router
│       ├── api.js                # Centralized Fetch API client
│       ├── store.js               # Reactive state management store
│       ├── components/           # Reusable UI component modules
│       └── views/                # Screen / Page view renderers
└── docs/
    ├── ARCHITECTURE.md
    ├── DATABASE.md
    ├── ROADMAP.md
    └── DECISIONS.md
```

---

## 3. Multi-Tenant Architecture & Data Isolation

### Context Model
NxtMov enforces multi-tenancy at the database query level. Every workspace (Personal or Consultancy) maps to an `Organization`.

- **Individual Workspace**: Created automatically upon user registration (`type = 'INDIVIDUAL'`). The organization has exactly 1 member (`owner_id`).
- **Consultancy Workspace**: Created by agency admins (`type = 'CONSULTANCY'`). Multiple team members belong to this organization with distinct RBAC roles.

### Enforcement Strategy
1. **Server-Side Active Tenant Context**:
   - The user selects an active workspace during session login or switches via workspace selection.
   - The active `organization_id` is encoded inside the JWT payload.
   - Dependency injection (`get_current_tenant`) unpacks the active `organization_id` on every authenticated request.
2. **Query Scoping**:
   - Every entity table containing tenant data (Companies, Contacts, Requirements, Candidates, Applications, Calls, Follow-ups) has a mandatory `organization_id` column indexed for fast lookup.
   - All SQLAlchemy queries MUST include `.filter(Entity.organization_id == current_tenant.id)`.

---

## 4. Authentication & Authorization Strategy

### Authentication Flow
- **Protocol**: OAuth2 Bearer token authentication using JSON Web Tokens (JWT).
- **Password Hashing**: `passlib[bcrypt]` or `argon2-cffi`. Plaintext passwords are never stored.
- **Session Tokens**: JWT containing `sub` (User ID), `org_id` (Active Tenant ID), `exp` (Expiration timestamp), and `role` (Role in active tenant).

### Role-Based Access Control (RBAC)
Roles defined within an `OrganizationMembership`:
- `ADMIN`: Full access to team management, settings, reports, candidates, requirements, applications.
- `RECRUITER`: Full access to operational CRM (Companies, Contacts, Requirements, Candidates, Submissions, Calls).
- `COUNSELOR`: Candidate-centric access (Candidates, Interviews, Applications).
- `CANDIDATE`: Candidate portal access (view submitted applications, schedule interviews, update resume).

---

## 5. API Architecture

All endpoints follow RESTful conventions under `/api/v1/`:

| Endpoint Prefix | Entity / Responsibility |
|---|---|
| `/api/v1/auth` | User registration, login, token refresh, workspace context switch |
| `/api/v1/users` | Current user profile, security settings |
| `/api/v1/organizations` | Organization profile, member invitations, team management |
| `/api/v1/companies` | Employers & Client companies CRUD |
| `/api/v1/contacts` | HR & Recruiter contacts CRUD |
| `/api/v1/candidates` | Candidate profiles CRUD |
| `/api/v1/requirements` | Job requisitions & openings CRUD |
| `/api/v1/calls` | Call logging, notes, outcomes |
| `/api/v1/followups` | "Next Move" follow-up task tracking |
| `/api/v1/applications` | Candidate applications & submission pipeline |
| `/api/v1/interviews` | Interview round scheduling & results |
| `/api/v1/offers` | Salary offers & negotiation records |
| `/api/v1/placements` | Confirmed placements & joining details |

---

## 6. Frontend Architecture

### Design & Tech Principles
- **Zero Heavy Build Dependencies**: Uses Vanilla ES Modules (`import / export`), natively supported by modern browsers.
- **Client-Side Routing**: Single Page Application (SPA) router mapping hash paths (`#/dashboard`, `#/companies`, `#/followups`) to view component functions.
- **State Store**: Lightweight reactive pub-sub state store (`store.js`) tracking current user, active workspace, current route, and active modal state.
- **API Client**: Centralized wrapper (`api.js`) utilizing `window.fetch` with automatic bearer token attachment, error handling, and session expiration handling.
- **Modern Styling**: CSS variables (`variables.css`) supporting modern dark/light themes, dynamic card elevations, glassmorphism, responsive grid & flexbox layouts.

---

## 7. UX Architecture & Navigation Taxonomy

### Unified Workspace Navigation
The main navigation dynamically adapts based on the active workspace type (`INDIVIDUAL` vs `CONSULTANCY`):

```text
Dashboard

Workspace
├── Companies
├── HR Contacts
├── Requirements / Opportunities
├── Candidates           [Hidden for Individual users if single-candidate mode]
├── Applications
├── Interviews
└── Placements

Activity ("Next Move Engine")
├── Calls
├── Follow-ups
└── Action Items

Organization             [Consultancy Mode Only]
├── Team Members
├── Students / Cohorts
└── Reports

Settings
├── Profile
├── Workspace Preferences
└── Security
```

### The "Next Move" UX Paradigm
Every key record view (Company, Contact, Application) prominently displays a **"Next Move Card"**:
- Current Status
- Pending Action / Follow-up
- Due Date
- Quick Action Button (e.g., "Log Call", "Schedule Interview", "Mark Done")

---

## 8. Security Architecture

1. **Authentication**: Mandatory password strength check (min 8 chars), secure bcrypt hashing.
2. **Authorization**: Server-side verification of `organization_id` on every DB read/write.
3. **Input Validation**: FastAPI Pydantic schema validation for all API inputs.
4. **SQL Injection Prevention**: Exclusive use of SQLAlchemy ORM parameterized queries.
5. **XSS Protection**: HTML encoding for user-generated content displayed in Vanilla JS components.
6. **CORS & Headers**: Strict CORS origin whitelisting, HTTP Security Headers (`X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`).
7. **Rate Limiting**: API request rate limiting using `slowapi` on auth and public endpoints.

---

## 9. Testing Strategy

### Backend Strategy
- **Unit Tests**: Pytest for individual schema validation, utility functions, password hashing.
- **API Integration Tests**: Pytest with FastAPI `TestClient` and in-memory SQLite database.
- **Multi-Tenant Security Tests**: Dedicated unit tests ensuring User A from Org 1 CANNOT query or mutate entities belonging to Org 2.

### Frontend & End-to-End Strategy
- Modular component rendering checks.
- E2E smoke tests covering complete candidate application & interview scheduling flows.

---

## 10. Git Strategy

- **Branching Model**: Trunk-based development with short-lived feature branches (`feature/auth`, `feature/crm-companies`).
- **Commit Conventions**: Conventional Commits style (`feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...`).
- **Environment Handling**: Configuration strictly driven by `.env` files. Secrets are NEVER committed.
