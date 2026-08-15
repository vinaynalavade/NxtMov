import os
import re
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.tenant import get_current_tenant, TenantContext
from app.models.organization import OrgRole
from app.models.candidate import Candidate, CandidateStatus, Document, DocumentType
from app.models.student_profile import StudentProfile
from app.models.resume import Resume, ResumeAnalysis
from app.schemas.resume import ResumeResponse, ResumeAnalysisResponse, ApplyAnalysisRequest
from app.services.resume_service import (
    extract_text_from_file_bytes,
    parse_resume_text,
    calculate_ats_score,
    calculate_profile_completeness
)
from app.core.config import STATIC_UPLOADS_DIR, RESUME_STORAGE_DIR, init_storage_directories
from app.services.notification_service import create_notification

router = APIRouter()
init_storage_directories()

def get_or_create_student_profile(db: Session, ctx: TenantContext):
    candidate = db.query(Candidate).filter(
        Candidate.organization_id == ctx.organization.id,
        Candidate.user_id == ctx.user.id
    ).first()

    if not candidate:
        candidate = Candidate(
            organization_id=ctx.organization.id,
            user_id=ctx.user.id,
            full_name=ctx.user.full_name,
            email=ctx.user.email,
            phone=ctx.user.phone,
            status=CandidateStatus.NEW
        )
        db.add(candidate)
        db.flush()

    profile = db.query(StudentProfile).filter(
        StudentProfile.organization_id == ctx.organization.id,
        StudentProfile.user_id == ctx.user.id
    ).first()

    if not profile:
        profile = StudentProfile(
            organization_id=ctx.organization.id,
            user_id=ctx.user.id,
            candidate_id=candidate.id,
            completeness_score=30
        )
        db.add(profile)
        db.flush()

    return candidate, profile

def build_resume_response(r: Resume, candidate_id: int) -> ResumeResponse:
    strengths = json.loads(r.strengths_json) if r.strengths_json else []
    improvements = json.loads(r.improvements_json) if r.improvements_json else []
    warnings = json.loads(r.warnings_json) if r.warnings_json else []
    likely_roles = json.loads(r.likely_roles_json) if r.likely_roles_json else []
    return ResumeResponse(
        id=r.id,
        candidate_id=candidate_id,
        file_name=r.file_name,
        file_type=r.file_type,
        file_url=f"/api/v1/resumes/{r.id}/file",
        file_size_bytes=r.file_size_bytes,
        is_current=r.is_current,
        quality_score=r.quality_score,
        ats_score=r.quality_score,
        career_domain=r.career_domain,
        likely_roles=likely_roles,
        domain_explanation=r.domain_explanation,
        strengths=strengths,
        improvements=improvements,
        warnings=warnings,
        created_at=r.created_at
    )

@router.get("/", response_model=List[ResumeResponse], summary="List Resumes for Current User / Candidate")
def list_resumes(
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    candidate, _ = get_or_create_student_profile(db, ctx)
    resumes = (
        db.query(Resume)
        .filter(
            Resume.organization_id == ctx.organization.id,
            Resume.candidate_id == candidate.id
        )
        .order_by(Resume.id.desc())
        .all()
    )

    return [build_resume_response(r, candidate.id) for r in resumes]

@router.post("/upload", response_model=ResumeResponse, summary="Upload Resume & Execute Intelligence Analysis")
async def upload_resume(
    file: UploadFile = File(...),
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    original_filename = file.filename or "resume.pdf"
    ext = os.path.splitext(original_filename)[1].lower()
    content = await file.read()

    if not content or len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded. Please select a valid resume document.")

    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(status_code=415, detail="Unsupported resume format. Upload PDF, DOCX, or TXT.")

    file_size_bytes = len(content)
    if file_size_bytes > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Resume file is too large (max 15MB).")

    candidate, profile = get_or_create_student_profile(db, ctx)

    # Save physical file securely with unique internal token
    stored_token = f"resume_{candidate.id}_{uuid.uuid4().hex[:8]}{ext}"
    saved_path = os.path.join(RESUME_STORAGE_DIR, stored_token)
    with open(saved_path, "wb") as f:
        f.write(content)

    file_url = f"/api/v1/resumes/{stored_token}"

    # Extract text & parse
    extracted_text = extract_text_from_file_bytes(content, original_filename)
    if not extracted_text or len(extracted_text.strip()) < 5:
        extracted_text = "Resume uploaded, but readable text could not be extracted. Please upload a standard PDF/DOCX/TXT file."

    parsed = parse_resume_text(extracted_text)
    ats_result = calculate_ats_score(extracted_text, parsed)

    # Mark existing resumes as not current
    db.query(Resume).filter(
        Resume.organization_id == ctx.organization.id,
        Resume.candidate_id == candidate.id
    ).update({"is_current": False})

    # Create new Resume record
    resume = Resume(
        organization_id=ctx.organization.id,
        candidate_id=candidate.id,
        file_name=original_filename,
        file_type=file.content_type or ext,
        file_url=file_url,
        file_size_bytes=file_size_bytes,
        extracted_text=extracted_text,
        is_current=True,
        quality_score=ats_result["ats_score"],
        career_domain=ats_result.get("career_domain"),
        likely_roles_json=json.dumps(ats_result.get("likely_roles", [])),
        domain_explanation=ats_result.get("domain_explanation"),
        strengths_json=json.dumps(ats_result["strengths"]),
        improvements_json=json.dumps(ats_result["improvements"]),
        warnings_json=json.dumps(ats_result.get("warnings", []))
    )
    db.add(resume)
    db.flush()

    # Sync Candidate document & resume_url
    candidate.resume_url = f"/api/v1/resumes/{resume.id}/file"
    doc = Document(
        organization_id=ctx.organization.id,
        candidate_id=candidate.id,
        file_name=original_filename,
        file_type=file.content_type or ext,
        file_url=f"/api/v1/resumes/{resume.id}/file",
        doc_type=DocumentType.RESUME
    )
    db.add(doc)

    # Create ResumeAnalysis record for user review ([Accept] [Edit] [Ignore])
    analysis = ResumeAnalysis(
        organization_id=ctx.organization.id,
        resume_id=resume.id,
        candidate_id=candidate.id,
        parsed_data_json=json.dumps(parsed),
        status="PENDING_REVIEW"
    )
    db.add(analysis)

    # Recalculate profile completeness
    comp_res = calculate_profile_completeness(candidate, profile)
    profile.completeness_score = comp_res["completeness_score"]

    db.commit()

    # Create Notification
    create_notification(
        db=db,
        organization_id=ctx.organization.id,
        user_id=ctx.user.id,
        title="Resume Analysis Completed",
        message=f"Analyzed '{original_filename}'. NxtMov ATS Score: {ats_result['ats_score']}/100.",
        notification_type="RESUME_ANALYZED",
        link_url="#/resume"
    )

    return build_resume_response(resume, candidate.id)

@router.get("/{id}/file", summary="Download / View Authenticated Resume Document")
def view_resume_file(
    id: int,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    resume = db.query(Resume).filter(
        Resume.organization_id == ctx.organization.id,
        Resume.id == id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume document not found.")

    # Locate exact physical file
    filename = os.path.basename(resume.file_url)
    file_path = os.path.join(RESUME_STORAGE_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Physical resume file could not be found on server storage.")

    media_type = "application/pdf"
    if resume.file_name.lower().endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif resume.file_name.lower().endswith(".txt"):
        media_type = "text/plain"

    return FileResponse(
        file_path,
        media_type=media_type,
        filename=resume.file_name,
        headers={"Content-Disposition": f'inline; filename="{resume.file_name}"'}
    )

@router.get("/{id}/analysis", response_model=ResumeAnalysisResponse, summary="Get Resume Parsing Intelligence Analysis")
def get_resume_analysis(
    id: int,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    analysis = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.organization_id == ctx.organization.id,
        ResumeAnalysis.resume_id == id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Resume analysis not found.")

    return ResumeAnalysisResponse(
        id=analysis.id,
        resume_id=analysis.resume_id,
        candidate_id=analysis.candidate_id,
        parsed_data=json.loads(analysis.parsed_data_json),
        status=analysis.status,
        created_at=analysis.created_at
    )

@router.post("/{id}/apply-analysis", summary="Accept/Apply Resume Extracted Data to Student Profile")
def apply_resume_analysis(
    id: int,
    req: ApplyAnalysisRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    analysis = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.organization_id == ctx.organization.id,
        ResumeAnalysis.resume_id == id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Resume analysis not found.")

    candidate, profile = get_or_create_student_profile(db, ctx)
    parsed = json.loads(analysis.parsed_data_json)
    accepted = req.accept_fields

    applied_items = []

    if ("name" in accepted or "full_name" in accepted) and parsed.get("full_name"):
        name_val = parsed["full_name"].strip()
        if name_val and len(name_val) >= 2:
            candidate.full_name = name_val
            ctx.user.full_name = name_val
            applied_items.append("Name")

    if "phone" in accepted and parsed.get("phone"):
        phone_val = parsed["phone"].strip()
        if phone_val and len(phone_val) >= 7:
            candidate.phone = phone_val
            ctx.user.phone = phone_val
            applied_items.append("Phone")

    if "skills" in accepted and parsed.get("skills"):
        existing = [s.strip() for s in (candidate.primary_skills or "").split(",") if s.strip()]
        for sk in parsed["skills"]:
            if sk not in existing:
                existing.append(sk)
        candidate.primary_skills = ", ".join(existing)
        applied_items.append("Skills")

        # Sync categorized skills into student profile breakdown
        cat_skills = parsed.get("categorized_skills", {})
        if cat_skills.get("Programming Languages"):
            profile.programming_languages = ", ".join(cat_skills["Programming Languages"])
        frameworks_list = cat_skills.get("Frontend & Web Frameworks", []) + cat_skills.get("Backend & API Frameworks", [])
        if frameworks_list:
            profile.frameworks = ", ".join(frameworks_list)
        if cat_skills.get("Quality Assurance & Automation"):
            profile.testing_tools = ", ".join(cat_skills["Quality Assurance & Automation"])
        if cat_skills.get("Databases & Storage"):
            profile.databases = ", ".join(cat_skills["Databases & Storage"])
        cloud_list = cat_skills.get("Cloud & Infrastructure", []) + cat_skills.get("DevOps & CI/CD", [])
        if cloud_list:
            profile.cloud_technologies = ", ".join(cloud_list)

    if "linkedin_url" in accepted and parsed.get("linkedin_url"):
        url_val = parsed["linkedin_url"].strip()
        if url_val.startswith("http://") or url_val.startswith("https://") or "linkedin.com" in url_val:
            profile.linkedin_url = url_val
            applied_items.append("LinkedIn")

    if "github_url" in accepted and parsed.get("github_url"):
        url_val = parsed["github_url"].strip()
        if url_val.startswith("http://") or url_val.startswith("https://") or "github.com" in url_val:
            profile.github_url = url_val
            applied_items.append("GitHub")

    if "education" in accepted:
        edu_entries = parsed.get("education_entries", [])
        if edu_entries and len(edu_entries) > 0:
            top_edu = edu_entries[0]
            profile.degree = top_edu.get("degree") or top_edu.get("display_text")
            profile.highest_qualification = top_edu.get("degree")
            if top_edu.get("specialization"):
                profile.specialization = top_edu.get("specialization")
            if top_edu.get("institution"):
                profile.college_university = top_edu.get("institution")
            if top_edu.get("year"):
                profile.graduation_year = top_edu.get("year")
            if top_edu.get("score"):
                profile.cgpa_or_percentage = top_edu.get("score")
            applied_items.append(f"Education ({len(edu_entries)} entries)")
        elif parsed.get("education") and len(parsed["education"]) > 0:
            profile.degree = parsed["education"][0]
            profile.highest_qualification = parsed["education"][0]
            applied_items.append("Education")

    analysis.status = "ACCEPTED"
    comp_res = calculate_profile_completeness(candidate, profile)
    profile.completeness_score = comp_res["completeness_score"]

    db.commit()

    summary_str = ", ".join(applied_items) if applied_items else "profile"
    return {"message": f"Successfully applied detected information ({summary_str}) to your profile.", "status": "ACCEPTED"}

@router.get("/current", response_model=Optional[ResumeResponse], summary="Get Current Active Resume")
def get_current_resume(
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    candidate, _ = get_or_create_student_profile(db, ctx)
    resume = (
        db.query(Resume)
        .filter(
            Resume.organization_id == ctx.organization.id,
            Resume.candidate_id == candidate.id,
            Resume.is_current == True
        )
        .first()
    )

    if not resume:
        return None

    return build_resume_response(resume, candidate.id)
