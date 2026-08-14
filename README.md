# NxtMov — Unified Job & Recruitment Management Platform

**NxtMov** (v1.0.0 Release Candidate) is a unified Job and Recruitment Management Platform built with Python (FastAPI), SQLAlchemy 2.0, Alembic, and a responsive Vanilla JavaScript Single Page Application (SPA).

NxtMov is designed around a single core philosophy:
> **"Always make the user's next move obvious."**

---

## 🌟 Core Features in v1.0.0

### 👤 Individual Job Seeker Mode
- **Personal Workspace**: Isolated workspace auto-provisioned upon registration.
- **Companies & HR CRM**: Client companies, recruiter contacts, designation, phone, email, and communication history.
- **Call Logging & Outcome Engine**: Log outbound/inbound calls, record outcomes (`Opportunity Available`, `Resume Requested`, `Not Relevant`), and auto-create "Next Move" follow-up tasks.
- **Next Moves Engine**: Categorizes action items into `Today`, `Overdue`, `Upcoming`, and `Completed`.
- **Opportunities & Applications**: Job requisitions, required skills, employment types, work modes (`REMOTE`, `HYBRID`, `ONSITE`), salary ranges, application pipeline stages (`APPLIED`, `SCREENING`, `INTERVIEWING`, `OFFERED`, `REJECTED`), and interview scheduling.

### 🏢 Consultancy & Recruitment Agency Mode (Preserved & Frozen)
- **Consultancy Workspaces**: Create agency organizations (`OrgType.CONSULTANCY`) and switch seamlessly between personal and consultancy contexts.
- **Team Management & RBAC**: Team member invitations across roles (`ADMIN`, `RECRUITER`, `COUNSELOR`, `CANDIDATE`).
- **Managed Candidate Database**: Talent pool tracking identity, experience, notice period, expected salary, current company, primary/secondary skills, and candidate documents (`RESUME`, `CERTIFICATE`, `ID_DOCUMENT`).
- **NxtMov Match Engine**: Deterministic candidate matching score (0–100%) evaluating skills (50%), experience (25%), location & work mode (15%), and salary budget (10%) with explicit match explanation (`pros` & `gaps`).
- **Submissions & Placements**: Client candidate submissions pipeline and placement recording.

### 📊 Excel & CSV Import Engine
- Import `HR_CONTACTS` or `CANDIDATES` from `.xlsx` and `.csv` files.
- Header synonym auto-mapping and duplicate checking (`NEW`, `EXACT_DUPLICATE`, `POSSIBLE_DUPLICATE`).
- Atomic database batch insertion.

---

## 🛠️ Technology Stack
- **Backend**: Python 3.11+ with **FastAPI**
- **Database & ORM**: **SQLAlchemy 2.0** ORM + **Alembic** Migrations (SQLite in WAL mode for local dev, PostgreSQL ready for prod)
- **Security**: JWT authentication, bcrypt password hashing with **SHA-256 pre-hashing**, and server-enforced tenant context dependency injection (`get_current_tenant`)
- **Frontend**: Modular Vanilla JavaScript (ES Modules), HTML5, Vanilla CSS custom properties (Zero build step overhead)
- **Testing**: **Pytest** with FastAPI `TestClient`

---

## 🚀 Quick Start (Local Development)

### 1. Setup Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### 2. Run Database Migrations
```powershell
cd backend
..\venv\Scripts\alembic upgrade head
cd ..
```

### 3. Start Backend Development Server (Recommended)
```powershell
.\venv\Scripts\python.exe backend\runserver.py
```

### 4. Start Frontend Development Server (Optional Independent Terminal)
```powershell
cd frontend
..\venv\Scripts\python.exe -m http.server 5500
```

### 5. Access Endpoints
- **Frontend App**: [http://127.0.0.1:5500](http://127.0.0.1:5500) (or via FastAPI backend at [http://127.0.0.1:8000](http://127.0.0.1:8000))
- **Backend API**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 6. Run Automated Test Suite
```powershell
.\venv\Scripts\pytest backend/tests
```


---

## 📄 License & Documentation
- Architectural Details: [`docs/ARCHITECTURE.md`](file:///x:/NxtMov/docs/ARCHITECTURE.md)
- Database ERD & Schema: [`docs/DATABASE.md`](file:///x:/NxtMov/docs/DATABASE.md)
- Engineering Decisions: [`docs/DECISIONS.md`](file:///x:/NxtMov/docs/DECISIONS.md)
- Release Roadmap: [`docs/ROADMAP.md`](file:///x:/NxtMov/docs/ROADMAP.md)
- Manual QA Regression Checklist: [`docs/REGRESSION_CHECKLIST.md`](file:///x:/NxtMov/docs/REGRESSION_CHECKLIST.md)
- v1.0.0 Release Notes: [`docs/RELEASE_NOTES.md`](file:///x:/NxtMov/docs/RELEASE_NOTES.md)
