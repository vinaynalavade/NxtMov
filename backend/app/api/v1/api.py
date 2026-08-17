from fastapi import APIRouter
from app.api.v1.endpoints import (
    health, auth, organizations, companies, contacts, activity,
    import_export, requirements, candidates, submissions, applications, dev_seed,
    profile, resumes, recommendations, notifications, interactions, mentor, admin
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(admin.router, prefix="/admin", tags=["Administrator Management & Approvals"])
api_router.include_router(profile.router, prefix="/profile", tags=["Student Talent Profile & Settings"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["Resume Intelligence & Parsing"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Intelligent Role Matching"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Server-Side Notifications"])
api_router.include_router(interactions.router, prefix="/interactions", tags=["Candidate HR Interactions"])
api_router.include_router(mentor.router, prefix="/mentor", tags=["Mentor Dashboard & Student Journey"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Consultancy Organizations & Team"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["HR Contacts"])
api_router.include_router(candidates.router, prefix="/candidates", tags=["Managed Candidates"])
api_router.include_router(submissions.router, tags=["Submissions & Placements"])
api_router.include_router(activity.router, prefix="/activity", tags=["Calls, Follow-ups & Dashboard"])
api_router.include_router(import_export.router, prefix="/import", tags=["Excel & CSV Import"])
api_router.include_router(requirements.router, prefix="/requirements", tags=["Job Requirements & Opportunities"])
api_router.include_router(applications.router, prefix="/applications", tags=["Applications & Interview Pipeline"])
api_router.include_router(dev_seed.router, prefix="/dev", tags=["Development Seed"])
