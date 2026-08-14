# NxtMov Database Schema & Domain Model

**Engine:** SQLAlchemy 2.0 ORM  
**Dialect:** SQLite (Development) / PostgreSQL (Production)  

---

## 1. Entity Relationship Overview

```text
               +-------------------+
               |       User        |
               +-------------------+
                         |
                         v 1:N
               +-------------------+
               |  Org Membership   |
               +-------------------+
                         ^
                         | N:1
               +-------------------+
               |   Organization    | <------------------------------------+
               +-------------------+                                      |
                         |                                                |
        +----------------+----------------+----------------+              | (Tenant Scoped)
        | 1:N            | 1:N            | 1:N            | 1:N          |
        v                v                v                v              |
  +-----------+    +-----------+    +-----------+    +-----------+        |
  | Company   |    | Candidate |    |  Requirement | | Follow-up |        |
  +-----------+    +-----------+    +-----------+    +-----------+        |
        |                |                |                |              |
    1:N |            1:N |            1:N |            1:N |              |
        v                v                v                v              |
  +-----------+    +-----------------------------------------------+      |
  |  Contact  |--->|                  Application                  |------+
  +-----------+    +-----------------------------------------------+
        |                                 |
    1:N |                             1:N |
        v                                 v
  +-----------+                    +---------------+
  |   Call    |                    |   Interview   |
  +-----------+                    +---------------+
                                          |
                                      1:1 |
                                          v
                                   +---------------+
                                   | Offer/Placement|
                                   +---------------+
```

---

## 2. Table Schemas & Specifications

### 2.1 Core System & Multi-Tenancy

#### `users`
Stores system accounts for login and identity.
- `id` (UUID/Integer, PK, Autoincrement)
- `email` (String, Unique, Index, Mandatory)
- `hashed_password` (String, Mandatory)
- `full_name` (String, Mandatory)
- `phone` (String, Optional)
- `is_active` (Boolean, Default True)
- `is_superuser` (Boolean, Default False)
- `created_at` (Timestamp UTC)
- `updated_at` (Timestamp UTC)

#### `organizations`
Represents isolated workspaces (Personal or Consultancy).
- `id` (UUID/Integer, PK)
- `name` (String, Mandatory)
- `slug` (String, Unique, Index, Mandatory)
- `type` (Enum: `INDIVIDUAL`, `CONSULTANCY`)
- `owner_id` (FK -> `users.id`)
- `created_at` (Timestamp UTC)

#### `organization_memberships`
Defines user access and roles inside an organization.
- `id` (UUID/Integer, PK)
- `organization_id` (FK -> `organizations.id`, Index)
- `user_id` (FK -> `users.id`, Index)
- `role` (Enum: `ADMIN`, `RECRUITER`, `COUNSELOR`, `CANDIDATE`)
- `created_at` (Timestamp UTC)
- *Unique Constraint:* `(organization_id, user_id)`

---

### 2.2 CRM Module (Companies & Contacts)

#### `companies`
Employer / client profiles scoped to an organization.
- `id` (UUID/Integer, PK)
- `organization_id` (FK -> `organizations.id`, Index)
- `name` (String, Mandatory)
- `website` (String, Optional)
- `industry` (String, Optional)
- `location` (String, Optional)
- `notes` (Text, Optional)
- `created_at` (Timestamp UTC)
- `updated_at` (Timestamp UTC)
- *Index:* `(organization_id, name)`

#### `contacts`
HR personnel, internal recruiters, or agency clients working at companies.
- `id` (UUID/Integer, PK)
- `organization_id` (FK -> `organizations.id`, Index)
- `company_id` (FK -> `companies.id`, Index)
- `name` (String, Mandatory)
- `designation` (String, Optional)
- `email` (String, Optional)
- `phone` (String, Optional)
- `linkedin_url` (String, Optional)
- `notes` (Text, Optional)
- `created_at` (Timestamp UTC)
- *Index:* `(organization_id, company_id)`

---

### 2.3 Recruitment & Talent Pool Module

#### `candidates`
Job seekers. Linked to a user account in Individual Mode, or managed records in Consultancy Mode.
- `id` (UUID/Integer, PK)
- `organization_id` (FK -> `organizations.id`, Index)
- `user_id` (FK -> `users.id`, Optional, Index) -- Present if candidate has a user account
- `full_name` (String, Mandatory)
- `email` (String, Mandatory)
- `phone` (String, Optional)
- `current_title` (String, Optional)
- `skills` (Text/JSON, Optional)
- `experience_years` (Float, Optional)
- `resume_url` (String, Optional)
- `status` (Enum: `ACTIVE`, `PLACED`, `INACTIVE`)
- `created_at` (Timestamp UTC)
- *Index:* `(organization_id, email)`

#### `job_requirements`
Job openings / opportunities posted by employers.
- `id` (UUID/Integer, PK)
- `organization_id` (FK -> `organizations.id`, Index)
- `company_id` (FK -> `companies.id`, Index)
- `contact_id` (FK -> `contacts.id`, Optional)
- `title` (String, Mandatory)
- `description` (Text, Optional)
- `location` (String, Optional)
- `employment_type` (Enum: `FULL_TIME`, `CONTRACT`, `PART_TIME`, `INTERNSHIP`)
- `min_salary` (Decimal, Optional)
- `max_salary` (Decimal, Optional)
- `status` (Enum: `OPEN`, `PAUSED`, `CLOSED`, `FILLED`)
- `created_at` (Timestamp UTC)
- *Index:* `(organization_id, status)`

---

### 2.4 Activity & "Next Move" Engine

#### `calls`
Logged phone calls or interactions with HR contacts / candidates.
- `id` (UUID/Integer, PK)
- `organization_id` (FK -> `organizations.id`, Index)
- `contact_id` (FK -> `contacts.id`, Optional, Index)
- `candidate_id` (FK -> `candidates.id`, Optional, Index)
- `user_id` (FK -> `users.id`) -- Recruiter who made the call
- `call_type` (Enum: `OUTBOUND`, `INBOUND`, `DISCOVERY`, `FOLLOWUP`)
- `outcome` (Enum: `CONNECTED`, `NO_ANSWER`, `VOICEMAIL`, `SCHEDULED_MEETING`, `REJECTED`)
- `notes` (Text, Mandatory)
- `called_at` (Timestamp UTC)

#### `followups`
Central task engine enforcing the "Next Move" workflow.
- `id` (UUID/Integer, PK)
- `organization_id` (FK -> `organizations.id`, Index)
- `assigned_user_id` (FK -> `users.id`, Index)
- `title` (String, Mandatory)
- `description` (Text, Optional)
- `due_date` (Timestamp UTC, Index)
- `status` (Enum: `PENDING`, `COMPLETED`, `CANCELLED`)
- `entity_type` (Enum: `COMPANY`, `CONTACT`, `REQUIREMENT`, `APPLICATION`)
- `entity_id` (Integer/UUID, Index)
- `created_at` (Timestamp UTC)
- *Index:* `(organization_id, due_date, status)`

---

### 2.5 Submissions, Pipeline & Placements

#### `applications`
Links candidates to job requirements along the recruitment lifecycle.
- `id` (UUID/Integer, PK)
- `organization_id` (FK -> `organizations.id`, Index)
- `job_requirement_id` (FK -> `job_requirements.id`, Index)
- `candidate_id` (FK -> `candidates.id`, Index)
- `stage` (Enum: `APPLIED`, `SUBMITTED`, `SCREENING`, `INTERVIEWING`, `OFFERED`, `PLACED`, `REJECTED`, `WITHDRAWN`)
- `notes` (Text, Optional)
- `applied_at` (Timestamp UTC)
- `updated_at` (Timestamp UTC)
- *Index:* `(organization_id, job_requirement_id, candidate_id)`

#### `interviews`
Scheduled interview rounds for an application.
- `id` (UUID/Integer, PK)
- `application_id` (FK -> `applications.id`, Index)
- `round_name` (String, Mandatory) -- e.g. "Technical Round 1"
- `scheduled_at` (Timestamp UTC, Index)
- `location_or_link` (String, Optional)
- `interviewer_names` (String, Optional)
- `outcome` (Enum: `SCHEDULED`, `PASSED`, `FAILED`, `RESCHEDULED`, `CANCELLED`)
- `feedback` (Text, Optional)
- `created_at` (Timestamp UTC)

#### `offers`
Job offers extended to candidates.
- `id` (UUID/Integer, PK)
- `application_id` (FK -> `applications.id`, Unique, Index)
- `offered_salary` (Decimal, Mandatory)
- `joining_date` (Date, Optional)
- `status` (Enum: `PENDING`, `ACCEPTED`, `DECLINED`, `REVISED`)
- `created_at` (Timestamp UTC)

#### `placements`
Confirmed successful placements.
- `id` (UUID/Integer, PK)
- `application_id` (FK -> `applications.id`, Unique, Index)
- `join_date` (Date, Mandatory)
- `billing_amount` (Decimal, Optional) -- Consultancy fee
- `status` (Enum: `ACTIVE`, `COMPLETED`, `EARLY_EXIT`)
- `created_at` (Timestamp UTC)

---

## 3. Database Migration Strategy

- **Alembic** manages all schema migrations.
- Every model change requires an explicit migration script generated via `alembic revision --autogenerate -m "description"`.
- Zero raw DDL strings in application code.
