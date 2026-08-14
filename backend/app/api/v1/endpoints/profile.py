import json
import os
import uuid
from typing import Dict, Any, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.tenant import get_current_tenant, TenantContext
from app.core.security import verify_password, get_password_hash
from app.models.user import User
from app.models.candidate import Candidate, CandidateStatus
from app.models.student_profile import StudentProfile
from app.schemas.student_profile import StudentProfileUpdate, StudentProfileResponse, AccountSettingsUpdate
from app.services.resume_service import calculate_profile_completeness

router = APIRouter()

AVATAR_TMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "static_uploads", "avatars")
os.makedirs(AVATAR_TMP_DIR, exist_ok=True)

def get_or_create_student_profile(db: Session, ctx: TenantContext) -> Tuple[Candidate, StudentProfile]:
    user = ctx.user
    org = ctx.organization

    # Find existing candidate record for this user or email in this org
    candidate = db.query(Candidate).filter(
        Candidate.organization_id == org.id,
        (Candidate.user_id == user.id) | (Candidate.email == user.email)
    ).first()

    if not candidate:
        candidate = Candidate(
            organization_id=org.id,
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            status=CandidateStatus.NEW,
            source="Student Self-Registration"
        )
        db.add(candidate)
        db.flush()

    if not candidate.user_id:
        candidate.user_id = user.id

    profile = db.query(StudentProfile).filter(
        StudentProfile.organization_id == org.id,
        StudentProfile.candidate_id == candidate.id
    ).first()

    if not profile:
        profile = StudentProfile(
            organization_id=org.id,
            candidate_id=candidate.id,
            user_id=user.id,
            city=candidate.location.split(",")[0].strip() if candidate.location and "," in candidate.location else candidate.location,
            country="India"
        )
        db.add(profile)
        db.flush()

    comp_res = calculate_profile_completeness(candidate, profile)
    profile.completeness_score = comp_res["completeness_score"]
    db.commit()
    db.refresh(profile)

    return candidate, profile

from typing import Tuple

@router.get("", response_model=StudentProfileResponse, summary="Get Current Student Talent Profile")
def get_profile(
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    candidate, profile = get_or_create_student_profile(db, ctx)
    comp_res = calculate_profile_completeness(candidate, profile)

    return StudentProfileResponse(
        id=profile.id,
        candidate_id=candidate.id,
        user_id=ctx.user.id,
        full_name=candidate.full_name,
        email=candidate.email,
        phone=candidate.phone,
        avatar_url=profile.avatar_url,
        city=profile.city,
        state=profile.state,
        country=profile.country,
        headline=profile.headline,
        career_objective=profile.career_objective,
        preferred_roles=profile.preferred_roles,
        preferred_locations=profile.preferred_locations,
        employment_preference=profile.employment_preference,
        expected_salary=profile.expected_salary or (float(candidate.expected_salary) if candidate.expected_salary else None),
        notice_period_days=profile.notice_period_days or candidate.notice_period_days,
        highest_qualification=profile.highest_qualification,
        degree=profile.degree,
        college_university=profile.college_university,
        graduation_year=profile.graduation_year,
        specialization=profile.specialization,
        cgpa_or_percentage=profile.cgpa_or_percentage,
        programming_languages=profile.programming_languages,
        frameworks=profile.frameworks,
        testing_tools=profile.testing_tools,
        databases=profile.databases,
        cloud_technologies=profile.cloud_technologies,
        soft_skills=profile.soft_skills,
        experience_json=profile.experience_json,
        projects_json=profile.projects_json,
        certifications_json=profile.certifications_json,
        linkedin_url=profile.linkedin_url,
        github_url=profile.github_url,
        portfolio_url=profile.portfolio_url,
        other_links_json=profile.other_links_json,
        email_notifications_enabled=profile.email_notifications_enabled,
        job_alerts_enabled=profile.job_alerts_enabled,
        completeness_score=comp_res["completeness_score"],
        missing_items=comp_res["missing_items"]
    )

@router.put("", response_model=StudentProfileResponse, summary="Update Student Talent Profile")
def update_profile(
    data: StudentProfileUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    candidate, profile = get_or_create_student_profile(db, ctx)

    # Sync fields to StudentProfile
    for key, val in data.model_dump(exclude_unset=True).items():
        if hasattr(profile, key):
            setattr(profile, key, val)

    # Sync key fields to Candidate model
    if data.preferred_roles:
        candidate.primary_skills = data.preferred_roles
    if data.expected_salary:
        candidate.expected_salary = data.expected_salary
    if data.notice_period_days:
        candidate.notice_period_days = data.notice_period_days
    if data.city:
        candidate.location = f"{data.city}, {data.state or 'India'}"

    comp_res = calculate_profile_completeness(candidate, profile)
    profile.completeness_score = comp_res["completeness_score"]

    db.commit()
    db.refresh(profile)

    return get_profile(ctx=ctx, db=db)

@router.put("/settings", summary="Update User Account Settings & Security")
def update_settings(
    data: AccountSettingsUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    user = ctx.user
    candidate, profile = get_or_create_student_profile(db, ctx)

    if data.full_name:
        user.full_name = data.full_name
        candidate.full_name = data.full_name
    if data.phone:
        user.phone = data.phone
        candidate.phone = data.phone
    if data.email and data.email != user.email:
        existing = db.query(User).filter(User.email == data.email, User.id != user.id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email address is already in use.")
        user.email = data.email
        candidate.email = data.email

    if data.new_password:
        if not data.old_password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is required to set a new password.")
        if not verify_password(data.old_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password.")
        user.hashed_password = get_password_hash(data.new_password)

    db.commit()
    return {"message": "Account settings updated successfully."}

@router.post("/avatar", summary="Upload Profile Picture Avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    candidate, profile = get_or_create_student_profile(db, ctx)

    ext = os.path.splitext(file.filename or "avatar.jpg")[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
        raise HTTPException(status_code=400, detail="Invalid image format. Supported formats: .jpg, .png, .webp, .svg")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Avatar image size exceeds 5MB limit.")

    file_name = f"avatar_{ctx.user.id}_{uuid.uuid4().hex[:8]}{ext}"
    saved_path = os.path.join(AVATAR_TMP_DIR, file_name)
    with open(saved_path, "wb") as f:
        f.write(content)

    avatar_url = f"/static/avatars/{file_name}"
    profile.avatar_url = avatar_url
    db.commit()

    return {"avatar_url": avatar_url, "message": "Profile picture updated successfully."}
